# AGENTS.md — CT Demo 通用框架开发指南

本文件用于指导编程助手在 `dev` 分支上启动 Control Tower（CT）Demo 开发。目标不是做一个强绑定物流场景的产品，而是做一个可嵌入既有业务系统的通用框架 / SDK：业务方可以保留自己的数据源、Agent、审批系统和 UI，只把 CT 作为任务编排、状态管理、权限代理、人机协同与可观测性的基础设施接入。

## 1. 开发目标与边界

### 1.1 Demo 要证明的核心能力

1. CT 能从外部异常来源接收结构化事件，也能由人通过 CT Agent 手动发布异常事件。
2. CT 能基于配置化 Policy 将异常路由成一个或多个任务，并分派给业务 Agent。
3. CT 能维护完整任务状态机，记录执行人 / 执行 Agent、耗时、关键进展和结果。
4. CT 能作为统一 Data Broker 代理数据查询，按 Agent 权限过滤数据。
5. CT 能在需要时通过 CT Agent 与人确认计划、请求审批、反馈进展。
6. CT 能通过 RabbitMQ 与各模块解耦，并保留替换消息中间件的接口抽象。

### 1.2 非目标

1. 不要把 Demo 写成物流专用产品；物流、仓储、供应链只能作为样例配置和样例数据。
2. 不要在 CT Core 中硬编码业务规则、业务实体或具体异常类型。
3. 不要使用 Kafka；本项目 Demo 和默认实现统一使用 RabbitMQ。
4. 不要让业务 Agent 直接访问 CT 管理的数据源；所有查询必须经由 Data Broker。
5. 不要把人机交互绑定到单一渠道；Slack、Web UI、CLI、企业 IM 都应通过端口 / 适配器接入。

## 2. 推荐架构

采用端口与适配器（Ports and Adapters）结构，核心领域逻辑不依赖 FastAPI、RabbitMQ、SQLite、Slack 或任何具体业务系统。

建议模块：

```text
ct_sdk/
  domain/                 # 领域模型：Event、Task、Agent、Policy、Approval、Progress
  ports/                  # 接口定义：EventBus、TaskStore、AgentGateway、HumanChannel、DataBroker
  application/            # 用例：接收异常、生成任务、分派任务、处理回调、升级人工
  adapters/
    api/                  # FastAPI REST API
    rabbitmq/             # RabbitMQ EventBus 实现
    persistence/          # SQLite / PostgreSQL 存储实现
    human/                # CT Agent 的人机交互适配器
    agents/               # HTTP Webhook AgentGateway
  observability/          # trace、日志、事件审计
examples/
  logistics_demo/         # 仅作为样例，不允许污染 ct_sdk 核心
```

如果现有仓库结构不同，可以按同样边界命名，但必须保持“核心领域无框架依赖”。

## 3. 消息总线要求：RabbitMQ

### 3.1 抽象接口

必须先定义通用 `EventBus` 端口，再实现 RabbitMQ 适配器。CT Core 只能依赖端口，不能直接依赖 `pika`、`aio-pika` 或 RabbitMQ 连接对象。

建议接口能力：

- `publish(topic, message, headers=None)`
- `subscribe(topic, handler, consumer_group=None)`
- `ack(delivery)`
- `nack(delivery, requeue=True)`
- `publish_to_dlq(message, reason)`

### 3.2 RabbitMQ Demo 拓扑

建议默认拓扑：

- Exchange：`ct.events`（topic exchange）
- Queue：`ct.anomalies`，绑定 `anomaly.*`
- Queue：`ct.tasks`，绑定 `task.*`
- Queue：`ct.progress`，绑定 `progress.*`
- Queue：`ct.approvals`，绑定 `approval.*`
- Queue：`ct.dlq`，用于失败消息和超过重试上限的任务

消息必须带：

- `trace_id`
- `event_id` 或 `task_id`
- `schema_version`
- `occurred_at`
- `source`

## 4. CT Agent：代表 CT 与人直接交互

必须新增 CT Agent 概念。它不是某个业务 Agent，而是 CT 的人机交互入口和出口，可作为 SDK 的默认组件实现。

### 4.1 CT Agent 职责

1. 接收人的自然语言或结构化请求，并转换为 CT 可处理的命令。
2. 支持人主动查询 CT 数据，例如异常详情、任务状态、执行耗时、当前处理人、历史进展。
3. 支持人主动发布异常事件，例如“某线路发生大面积延误”。
4. 在 CT 需要人工参与时，向人确认计划、请求审批或收集补充参数。
5. 向人反馈任务进展、关键节点、失败原因、回滚结果和最终结论。
6. 保留与多种渠道集成的能力：REST API、Web UI、Slack、企业 IM、CLI。

### 4.2 CT Agent 设计原则

- CT Agent 调用 CT Application Service，不直接修改数据库。
- CT Agent 输出的命令必须结构化，例如 `CreateAnomalyEvent`、`ApprovePlan`、`RejectAction`、`RequestTaskStatus`。
- CT Agent 可使用 LLM 做意图解析，但最终动作必须经过权限校验和结构化参数校验。
- 对高风险动作，CT Agent 必须复述计划并等待人确认。
- Demo 中可以先实现 REST / CLI 适配器，后续再接 Slack 或 Web UI。

## 5. 任务状态机与进展回传

任务状态机是 Demo 的核心展示点，必须实现为通用状态机，而不是散落在业务代码里的 if/else。

### 5.1 推荐状态

```text
CREATED
  -> DISPATCHED
  -> IN_PROGRESS
  -> AWAITING_HUMAN
  -> COMPLETED
  -> FAILED
  -> CANCELLING
  -> CANCELLED
  -> ROLLING_BACK
  -> ROLLED_BACK
```

允许从 `IN_PROGRESS` 进入 `AWAITING_HUMAN`、`FAILED` 或 `COMPLETED`。允许从 `FAILED` 进入 `ROLLING_BACK`。状态迁移必须记录审计事件。

### 5.2 执行中任务必须展示的字段

当任务处于 `DISPATCHED`、`IN_PROGRESS`、`AWAITING_HUMAN`、`ROLLING_BACK` 时，API 必须能返回：

- `task_id`
- `task_type`
- `status`
- `assignee_type`：`agent` / `human` / `ct_agent` / `system`
- `assignee_id`
- `assignee_display_name`
- `started_at`
- `last_progress_at`
- `elapsed_seconds`
- `deadline_at`
- `progress_percent`（可为空）
- `current_stage`（例如“查询承运商状态”“等待人工审批”“执行补偿动作”）
- `progress_events`（按时间排序的关键节点）

`elapsed_seconds` 应由 `started_at` 动态计算，不要只在数据库里存静态值。

### 5.3 进展事件

业务 Agent、CT Agent、系统调度器都可以回传进展。建议事件结构：

```json
{
  "progress_id": "uuid",
  "task_id": "uuid",
  "trace_id": "uuid",
  "source_type": "agent",
  "source_id": "logistics_agent_001",
  "stage": "checking_carrier_status",
  "message": "已完成承运商状态查询，发现 3 个运单受影响",
  "progress_percent": 40,
  "occurred_at": "ISO8601",
  "metadata": {}
}
```

进展事件必须 append-only 存储，不能覆盖旧进展。

## 6. 通用 SDK 数据模型

优先使用通用命名，避免物流定制字段进入核心模型。

### 6.1 AnomalyEvent

- `event_id`
- `event_type`
- `severity`
- `source`
- `trace_id`
- `occurred_at`
- `payload`
- `context_snapshot`
- `schema_version`

### 6.2 AgentCard

- `agent_id`
- `display_name`
- `version`
- `capabilities`
- `endpoint`
- `webhook_path`
- `data_scopes`
- `max_concurrent_tasks`
- `metadata`

### 6.3 Task

- `task_id`
- `parent_event_id`
- `task_type`
- `status`
- `priority`
- `trace_id`
- `assigned_to`
- `created_at`
- `started_at`
- `completed_at`
- `deadline_at`
- `input_payload`
- `result_payload`
- `policy_version`

### 6.4 ApprovalRequest

- `approval_id`
- `task_id`
- `requested_by`
- `approver_role`
- `status`
- `plan_summary`
- `risk_level`
- `options`
- `decision`
- `created_at`
- `decided_at`

## 7. API 最小集合

Demo 至少实现以下 API。路径可以调整，但语义必须保留。

### 7.1 CT Agent / Human API

- `POST /api/v1/ct-agent/messages`：人向 CT Agent 发消息或结构化命令。
- `POST /api/v1/anomalies`：人或外部系统发布异常事件。
- `GET /api/v1/tasks/{task_id}`：查询任务详情、执行人、耗时和进展。
- `GET /api/v1/tasks`：按状态、执行人、事件、时间范围查询任务。
- `POST /api/v1/approvals/{approval_id}/decision`：人工审批。

### 7.2 Business Agent API

- `POST /api/v1/agents/register`：注册业务 Agent。
- `POST /api/v1/agents/{agent_id}/heartbeat`：心跳。
- `POST /api/v1/tasks/{task_id}/result`：提交任务结果。
- `POST /api/v1/tasks/{task_id}/progress`：回传进展。
- `POST /api/v1/tasks/{task_id}/query`：经 CT Data Broker 查询数据。
- `POST /api/v1/tasks/{task_id}/escalate`：请求人工介入。

## 8. Policy 与可配置性

Policy 必须配置化，不能硬编码。Demo 可使用 YAML，生产可迁移到数据库。

Policy 至少表达：

- 哪类 `event_type` 触发哪些任务。
- 顺序 / 并行路由。
- Agent capability 匹配规则。
- 超时配置。
- 需要人工审批的动作。
- 回滚 / 补偿策略。
- 进展回传要求，例如必须在某些阶段汇报。

样例 Policy 应放在 `examples/` 下，核心 SDK 不引用样例业务名。

## 9. 权限与数据代理

1. 所有 Agent 必须先注册并获得身份。
2. CT 必须基于 `AgentCard.data_scopes` 和 ACL 校验查询权限。
3. Data Broker 返回数据时应支持字段级或实体级过滤。
4. 查询请求、拒绝原因和返回摘要必须写入审计日志。
5. CT Agent 代表人查询时，也必须校验人的角色和权限。

## 10. 可观测性与审计

必须记录 append-only 事件：

- 异常事件接收。
- Policy 匹配和路由决策。
- 任务状态迁移。
- 任务进展回传。
- Agent 注册和心跳异常。
- 人工审批请求和决策。
- 数据查询与权限拒绝。
- 回滚和补偿执行。

日志和事件中必须传递 `trace_id`。Demo 可以使用 SQLite 存储事件；如果增加 OpenTelemetry，请保持为可选依赖。

## 11. Demo 开发顺序建议

1. 建立领域模型、端口接口和内存实现，先跑通无外部依赖的单元测试。
2. 实现任务状态机和进展事件存储。
3. 实现 RabbitMQ EventBus 适配器，并提供 Docker Compose。
4. 实现 FastAPI 最小 API。
5. 实现 CT Agent 的 REST / CLI Demo 入口。
6. 实现一个样例业务 Agent，用 HTTP Webhook 接任务、回传进展和结果。
7. 添加样例 Policy 和样例异常事件。
8. 添加任务详情页面或简单 CLI，展示执行人、耗时和进展。

## 12. 编码约束

- 核心领域代码不得导入 FastAPI、RabbitMQ 客户端、数据库 ORM 或业务样例模块。
- 适配器可以依赖具体技术，但必须通过端口与核心交互。
- 新增功能必须有单元测试；状态机迁移和权限校验必须重点测试。
- 所有时间使用 timezone-aware UTC datetime。
- 所有外部输入必须做 schema 校验。
- 不要在 import 周围添加 try/catch。
- 配置文件和样例数据中可以出现物流示例，但核心模型、接口和服务命名必须保持通用。

## 13. 验收标准

Demo 第一阶段完成时，应能通过以下流程演示：

1. 人通过 CT Agent 或 API 发布一个异常事件。
2. CT 通过 RabbitMQ 收到事件并匹配 Policy。
3. CT 创建任务并分派给注册的业务 Agent。
4. 任务进入 `IN_PROGRESS` 后，可以查询到执行 Agent、已耗时多久和当前阶段。
5. 业务 Agent 至少回传两次进展事件。
6. CT Agent 能把进展反馈给人。
7. 如任务要求审批，CT Agent 能向人确认计划并提交审批结果。
8. 任务完成后，CT 记录结果和完整审计链路。
