信息已经足够了，现在开始设计。先给整体蓝图，再逐层拆解工程细节。下面逐层拆解工程细节，按你提的5个方向组织。

---

## 一、监控与检测层

你们现有的 Ontology→SQL Agent 直接作为这一层的查询引擎，封装成一个内部 HTTP 服务（FastAPI），对 CT 暴露一个 `/query` 接口，接收 Ontology 语法字符串，返回结构化结果。

**调度器**用 APScheduler（Python 内嵌，无需独立服务），每条异常规则配置独立的 cron 表达式，触发后调用查询引擎，拿到数据后经规则引擎判断是否触发异常。

**异常定义格式**（对应你的 5.1）：

```yaml
anomaly_id: shipment_delay_critical
display_name: 严重运输延误
severity: critical          # critical / high / medium / low
detection:
  schedule: "*/15 * * * *"
  query: |                  # Ontology 语法，直接传给现有引擎
    FIND Shipment
    WHERE eta_delay > 24h
      AND status NOT IN [delivered, cancelled]
  threshold:
    type: count             # count / value / rate
    operator: ">"
    value: 0
  context_fetch:            # 触发时额外拉取的上下文数据，放入 Event
    - FIND Shipment WHERE ...
    - FIND Carrier WHERE ...
```

判断阈值后，发布一个**结构化 Event** 到事件总线：

```json
{
  "event_id": "uuid",
  "anomaly_id": "shipment_delay_critical",
  "severity": "critical",
  "timestamp": "ISO8601",
  "trace_id": "uuid",          // 全链路追踪，从这里生成，一直带到最后
  "context_snapshot": { ... }  // 已经拉好的数据，避免后面重复查
}
```

---

## 二、事件总线

Demo 阶段直接用 **Redis Streams**：单进程，`pip install redis`，10分钟能接通。Key 设计：

- `ct:events:anomalies` — 主异常流
- `ct:events:dlq` — 死信队列（超过3次重试后转入）

CT Core 以 Consumer Group `ct-orchestrator` 消费，保证每个 Event 只被处理一次。生产阶段直接换 Kafka，接口层不需要改动（抽象成 `EventBus` 接口）。

---

## 三、Control Tower 核心五个模块

### Policy Engine（对应 5.2）

纯配置驱动，**不经过 LLM 决策**（对应你的 1.2），路由是确定性的：

```yaml
# policy.yaml
policies:
  - anomaly_id: shipment_delay_critical
    routing:
      strategy: sequential     # sequential / parallel
      agents:
        - agent_id: logistics_agent
          task_type: investigate_delay
          timeout_minutes: 30
        - agent_id: warehouse_agent  
          task_type: adjust_forecast
          timeout_minutes: 60
          depends_on: logistics_agent  # 上一个完成后才触发
    escalation:
      triggers:
        - confidence_lt: 0.7
        - action_in: [cancel_shipment, emergency_reroute]  # 不可逆操作
        - no_response_minutes: 30
      escalate_to:
        type: human
        role: ops_manager
        channel: slack
        timeout_hours: 2         # 超时后自动升级到更高级别
    rollback:
      enabled: true
      strategy: saga
```

配置文件支持热加载（`watchdog` 监听文件变化，无需重启服务）。每次配置变更版本化存入 DB，便于审计回溯。

### Agent Registry（对应 3.2）

Agent 注册时提交 **Agent Card**（JSON）：

```json
{
  "agent_id": "logistics_agent_001",
  "name": "物流运输 Agent",
  "department": "logistics",
  "version": "1.2.0",
  "capabilities": ["investigate_delay", "reroute_shipment", "update_carrier"],
  "endpoint": "https://logistics-agent.internal",
  "webhook_path": "/ct/tasks",
  "data_scope": [
    "entity:shipment:logistics",
    "entity:carrier:all"
  ],
  "max_concurrent_tasks": 5
}
```

CT 验证后颁发 JWT，存入 Registry 表。Agent 每 30s 发心跳（`POST /ct/agents/{id}/heartbeat`），CT 监控 Agent 存活状态——如果 Agent 宕机，对应任务自动进入超时流程。

**ACL 表**单独维护：`agent_id → [allowed_data_entities]`，和 Agent Card 里的 `data_scope` 对应。Data Broker 查询时以这张表做过滤。

### Task Orchestrator + SAGA（对应 4.1 / 4.2）

这是 CT 最核心的模块。**任务状态机**：

```
CREATED → DISPATCHED → IN_PROGRESS → AWAITING_HUMAN
                                   ↘ COMPLETED
                                   ↘ FAILED → ROLLING_BACK → ROLLED_BACK
```

**SAGA 设计**：每个任务步骤存两个 payload，正向 action 和补偿 action：

```
task_steps 表：
step_id | task_id | agent_id | forward_action | compensating_action | status | result
```

回退时倒序执行各步骤的 `compensating_action`。物流场景举例：

| 步骤 | 正向 Action | 补偿 Action |
|------|------------|------------|
| 1 | 重新路由运单 | 恢复原路由 |
| 2 | 通知仓库调整库存预期 | 撤回通知，恢复原预期 |
| 3 | 更新 ETA | 恢复原 ETA |

**CT→Agent 的通信不是直接 API 调用**，而是：
1. CT 把任务写入 DB（状态 `CREATED`）
2. CT 调用 Agent 的 Webhook（HTTP POST）推送任务
3. 如果 Webhook 失败：指数退避重试（1s/2s/4s），3次后任务转 DLQ，告警
4. Agent 异步处理，通过回调接口通知 CT 结果

这样 CT 即使重启，也能从 DB 恢复所有进行中的任务，不丢状态。

### Data Broker（对应 3.3 权限隔离）

CT 是**唯一有权限查询各数据源的中心节点**，业务 Agent 不直接访问任何数据库。

两个场景：
- **任务下发时**：CT 提前拉取相关数据放入 `context_snapshot`，Agent 直接用，无需回调查询
- **Agent 主动查询时**（对应 2.1）：Agent 调用 `POST /ct/tasks/{id}/query`，CT 检查该 Agent 的 ACL，只返回其权限范围内的数据

跨部门查询：Agent A 请求 Agent B 的数据域 → CT 直接拒绝（403）并记录日志，不存在"绕过"的可能。

### Escalation Manager（对应 5.3）

触发条件在 policy.yaml 里配置（见上）。升级后：

1. CT 暂停该任务步骤，状态变为 `AWAITING_HUMAN`
2. 向人工推送**结构化审批请求**（含：异常摘要、Agent 建议 action、风险评级、上下文数据）
3. 人工在 UI/Slack 上选择：批准 / 拒绝 / 修改参数
4. CT 收到响应，记录审批结果（含人工 ID、时间戳、决策），继续或终止任务
5. 如人工超时未响应：按 policy 配置决定是升级到更高角色，还是自动失败

---

## 四、通信协议设计（对应 3.1 / 3.2）

**CT 下发任务**（POST 到 Agent 的 `webhook_path`）：

```json
{
  "task_id": "uuid",
  "task_type": "investigate_delay",
  "priority": "critical",
  "trace_id": "uuid",
  "context": {
    "affected_shipments": [...],
    "data_snapshot": { ... }
  },
  "actions_allowed": ["query_ct", "update_shipment_status"],
  "actions_requiring_approval": ["cancel_shipment", "emergency_reroute"],
  "deadline": "ISO8601",
  "callback": {
    "result":   "https://ct.internal/api/v1/tasks/{task_id}/result",
    "query":    "https://ct.internal/api/v1/tasks/{task_id}/query",
    "escalate": "https://ct.internal/api/v1/tasks/{task_id}/escalate"
  }
}
```

**Agent 回调 CT 的三个接口**：

- `POST /result`：任务完成，带 `{status, actions_taken, confidence, result}`
- `POST /query`：查数据，带 `{question, ontology_query}`，CT 鉴权后代查返回
- `POST /escalate`：Agent 主动请求人工介入，带 `{reason, risk_level, proposed_action}`

Auth 统一用 Bearer JWT，CT 注册时颁发，Payload 含 `{agent_id, scope: ["task:read", "ct:query", "data:logistics"]}`，每个接口按 scope 鉴权。

---

## 五、可观测性（对应 4.3）

每个事件、状态变更、路由决策都写入 `event_store` 表（append-only，不允许 UPDATE/DELETE）：

```
event_id | trace_id | span_id | timestamp | event_type | source | task_id | payload (JSON)
```

`trace_id` 从 Event 发布时生成，一路透传到所有 Agent 回调。用 OpenTelemetry Python SDK 自动 instrument FastAPI + Redis 调用，Span 导出到 **Jaeger**（免费自部署，Docker 一行命令起来）。

Demo 阶段监控面板可以先做一个简单的 FastAPI + 前端页面，展示：异常触发率、任务完成率、升级率、Agent 响应时间。

---

## 技术栈建议（3人团队 / Demo → 生产）

| 组件 | Demo | 生产路径 |
|---|---|---|
| 后端框架 | FastAPI（Python） | 不变 |
| 事件总线 | Redis Streams | Kafka |
| 状态 DB | SQLite → PostgreSQL | PostgreSQL |
| 调度器 | APScheduler（嵌入） | Celery Beat |
| 追踪 | OpenTelemetry + Jaeger | 同，或接入 DataDog |
| 人工介入 | Slack Bot（最快） | 自研审批 UI |
| Agent 注册 | REST API + DB 表 | 同，加 UI |

---

## 一个值得提前想清楚的决策

现在架构里有一个核心张力：**CT 的 `context_snapshot`应该预取多少数据**？

- 预取太多：CT 和数据层耦合深，每种异常都要写专门的取数逻辑
- 预取太少：Agent 频繁回调 CT 查数，接口压力大，链路变长

建议的平衡：**按 `data_scope` 批量预取，让 Agent Card 里声明"我处理这类任务需要哪些实体"**，CT 按声明自动拼装 snapshot，不需要为每种异常手写取数逻辑。这个设计比较优雅，也和你们的 Ontology 语法天然契合。

如果这份蓝图方向确认，下一步可以把每个模块的接口协议定义成文档，带去和物流专家讨论时验证业务逻辑的合理性。