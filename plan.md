# CT Demo 开发跟踪计划

本文档结合 `AGENTS.md` 中的目标架构与当前仓库已实现内容，用于跟踪 Control Tower（CT）Demo 从“前台 Mock + 内存核心雏形”演进为“可嵌入既有业务系统的通用框架 / SDK”的阶段性计划。

## 1. 总体目标

CT Demo 的第一阶段目标是证明以下端到端链路：

1. 人或外部系统可以发布结构化异常事件。
2. CT 基于配置化 Policy 将异常路由为一个或多个通用任务。
3. CT 维护任务状态机、执行人 / Agent、耗时、进展与结果。
4. 业务 Agent 只能通过 CT Data Broker 查询数据，并受权限控制。
5. CT Agent 作为人机交互入口，支持发布异常、查询状态、请求审批与反馈进展。
6. 模块之间通过 `EventBus` 端口解耦，默认 Demo 适配 RabbitMQ。

## 2. 当前实现盘点

### 2.1 已完成

- [x] 项目基础：`pyproject.toml` 已配置 Python 包、FastAPI、pytest、uvicorn 等基础依赖。
- [x] Demo UI 入口：`src/iscct/app.py` 已提供 FastAPI 应用、静态资源挂载、首页和健康检查接口。
- [x] 通用消息模型雏形：`src/iscct/domain.py` 已定义 `QueueMessage`、`QueueDeliveryStatus`。
- [x] Agent 通用模型雏形：`src/iscct/domain.py` 已定义 `AgentCard`、`AgentCapability`，覆盖能力、端点、数据范围、并发上限与元数据。
- [x] 端口抽象雏形：`src/iscct/ports.py` 已定义 `EventBus`、`AgentRuntime`、`AgentRegistry`。
- [x] 内存 EventBus：`src/iscct/memory.py` 已实现 `InMemoryEventBus`，支持发布、订阅、ack、nack、DLQ 发布。
- [x] 内存 Agent Registry：`src/iscct/memory.py` 已实现 Agent 注册、查询和列表能力。
- [x] 任务领域模型雏形：`src/iscct/tasking.py` 已定义 `TaskStatus`、`AssigneeType`、`TaskProgressEvent`、`Task`。
- [x] 任务进展 append-only 存储雏形：`InMemoryTaskStore.append_progress()` 会追加进展事件，并更新任务快照字段 `current_stage` 与 `progress_percent`。
- [x] 任务分派服务雏形：`TaskDispatchService` 支持创建任务、分派任务并发布 `task.dispatched` 事件。
- [x] 基础单元测试：`tests/test_memory.py` 已覆盖 Agent 注册、任务创建 / 分派、进展追加与任务快照更新。

### 2.2 与 AGENTS.md 目标的主要差距

- [ ] 目录结构尚未按 `domain/`、`ports/`、`application/`、`adapters/`、`observability/` 拆分；当前核心代码集中在 `src/iscct/*.py`。
- [ ] 缺少 `AnomalyEvent`、`ApprovalRequest`、Policy 等关键领域模型。
- [ ] `TaskStore`、`HumanChannel`、`DataBroker`、`AgentGateway` 等端口尚未定义完整。
- [ ] 任务状态机尚未集中封装迁移规则与审计记录，目前仅在分派时直接替换状态。
- [ ] 任务详情查询尚未输出 `last_progress_at`、动态 `elapsed_seconds`、`progress_events` 等完整展示字段。
- [ ] RabbitMQ 适配器和 Docker Compose 尚未实现。
- [ ] FastAPI 最小业务 API 尚未实现，目前只有首页和 `/api/health`。
- [ ] CT Agent 概念、结构化命令、REST / CLI 入口尚未实现。
- [ ] Data Broker 权限校验、字段级 / 实体级过滤、查询审计尚未实现。
- [ ] 可观测性与 append-only 审计事件尚未建立统一模型和存储。
- [ ] 样例 Policy、样例异常事件、样例业务 Agent 尚未放入 `examples/`。

## 3. 分阶段开发计划

### Phase 0：整理架构边界与现有代码

目标：在不破坏现有 Demo UI 的前提下，将代码组织逐步靠近端口与适配器架构。

- [ ] 建立推荐目录结构：
  - [ ] `src/iscct/domain/`
  - [ ] `src/iscct/ports/`
  - [ ] `src/iscct/application/`
  - [ ] `src/iscct/adapters/`
  - [ ] `src/iscct/observability/`
- [ ] 将现有 `domain.py`、`tasking.py`、`ports.py`、`memory.py` 迁移或拆分到对应包中。
- [ ] 保留兼容导入或一次性更新测试与应用导入。
- [ ] 明确核心领域层禁止依赖 FastAPI、RabbitMQ 客户端、数据库 ORM、样例业务模块。
- [ ] 补充架构 README，说明核心层、应用层、适配器层之间的依赖方向。

验收标准：

- [ ] `pytest` 全部通过。
- [ ] 核心领域代码中无 FastAPI / RabbitMQ / SQLite / 样例业务导入。

### Phase 1：补齐通用领域模型与内存端口

目标：先用无外部依赖的内存实现跑通核心用例。

- [ ] 新增 `AnomalyEvent` 领域模型，字段包括：
  - [ ] `event_id`
  - [ ] `event_type`
  - [ ] `severity`
  - [ ] `source`
  - [ ] `trace_id`
  - [ ] `occurred_at`
  - [ ] `payload`
  - [ ] `context_snapshot`
  - [ ] `schema_version`
- [ ] 新增 `ApprovalRequest` 领域模型，字段包括：
  - [ ] `approval_id`
  - [ ] `task_id`
  - [ ] `requested_by`
  - [ ] `approver_role`
  - [ ] `status`
  - [ ] `plan_summary`
  - [ ] `risk_level`
  - [ ] `options`
  - [ ] `decision`
  - [ ] `created_at`
  - [ ] `decided_at`
- [ ] 定义并实现内存版端口：
  - [ ] `TaskStore`
  - [ ] `AnomalyEventStore`
  - [ ] `PolicyStore`
  - [ ] `ApprovalStore`
  - [ ] `AuditLogStore`
  - [ ] `DataBroker`
  - [ ] `HumanChannel`
  - [ ] `AgentGateway`
- [ ] 所有时间字段统一使用 timezone-aware UTC datetime。
- [ ] 为模型默认值、trace 传递、基础存储行为补充单元测试。

验收标准：

- [ ] 可以在内存中创建异常事件、任务、审批请求、审计事件。
- [ ] 领域模型不包含物流或其他业务专用字段。

### Phase 2：任务状态机与进展详情

目标：将任务状态迁移与进展回传变成核心展示能力。

- [ ] 实现集中式 `TaskStateMachine`，禁止状态迁移散落在业务代码中。
- [ ] 明确合法状态迁移：
  - [ ] `CREATED -> DISPATCHED`
  - [ ] `DISPATCHED -> IN_PROGRESS`
  - [ ] `IN_PROGRESS -> AWAITING_HUMAN`
  - [ ] `IN_PROGRESS -> COMPLETED`
  - [ ] `IN_PROGRESS -> FAILED`
  - [ ] `FAILED -> ROLLING_BACK`
  - [ ] `ROLLING_BACK -> ROLLED_BACK`
  - [ ] `DISPATCHED / IN_PROGRESS / AWAITING_HUMAN -> CANCELLING -> CANCELLED`
- [ ] 非法迁移必须抛出明确领域错误。
- [ ] 每次状态迁移写入 append-only 审计事件。
- [ ] 进展事件继续保持 append-only，不允许覆盖旧事件。
- [ ] 实现任务详情投影，执行中任务必须返回：
  - [ ] `task_id`
  - [ ] `task_type`
  - [ ] `status`
  - [ ] `assignee_type`
  - [ ] `assignee_id`
  - [ ] `assignee_display_name`
  - [ ] `started_at`
  - [ ] `last_progress_at`
  - [ ] 动态计算的 `elapsed_seconds`
  - [ ] `deadline_at`
  - [ ] `progress_percent`
  - [ ] `current_stage`
  - [ ] 按时间排序的 `progress_events`
- [ ] 为合法 / 非法状态迁移、耗时计算、进展排序补充重点测试。

验收标准：

- [ ] 任务进入 `IN_PROGRESS` 后可以查询执行 Agent、已耗时多久、当前阶段与历史进展。
- [ ] 状态迁移和进展回传都能在审计日志中追踪到同一个 `trace_id`。

### Phase 3：Policy 路由与任务编排

目标：从硬编码任务创建演进为配置化 Policy 驱动。

- [ ] 定义通用 Policy 模型，至少表达：
  - [ ] `event_type` 匹配规则
  - [ ] 触发任务列表
  - [ ] 顺序 / 并行路由
  - [ ] Agent capability 匹配规则
  - [ ] 超时配置
  - [ ] 人工审批规则
  - [ ] 回滚 / 补偿策略
  - [ ] 必须回传进展的阶段
- [ ] 实现 YAML Policy 加载器，核心 SDK 不引用样例业务名。
- [ ] 实现 `ReceiveAnomalyEvent` 应用服务：
  - [ ] 校验异常事件输入
  - [ ] 存储异常事件
  - [ ] 匹配 Policy
  - [ ] 创建任务
  - [ ] 写入路由审计事件
  - [ ] 通过 EventBus 发布任务事件
- [ ] 在 `examples/` 添加样例 Policy 和样例异常事件。
- [ ] 补充 Policy 匹配、任务生成、无匹配策略、多个任务路由测试。

验收标准：

- [ ] 发布一个样例异常事件后，CT 能根据 YAML Policy 创建一个或多个任务。
- [ ] 核心代码中没有物流字段或物流规则硬编码。

### Phase 4：FastAPI 最小业务 API

目标：补齐 AGENTS.md 要求的最小 API 集合，作为 Demo 和 SDK 默认适配器。

- [ ] CT Agent / Human API：
  - [ ] `POST /api/v1/ct-agent/messages`
  - [ ] `POST /api/v1/anomalies`
  - [ ] `GET /api/v1/tasks/{task_id}`
  - [ ] `GET /api/v1/tasks`
  - [ ] `POST /api/v1/approvals/{approval_id}/decision`
- [ ] Business Agent API：
  - [ ] `POST /api/v1/agents/register`
  - [ ] `POST /api/v1/agents/{agent_id}/heartbeat`
  - [ ] `POST /api/v1/tasks/{task_id}/result`
  - [ ] `POST /api/v1/tasks/{task_id}/progress`
  - [ ] `POST /api/v1/tasks/{task_id}/query`
  - [ ] `POST /api/v1/tasks/{task_id}/escalate`
- [ ] 外部输入使用 Pydantic schema 校验。
- [ ] API 层只调用 application service，不直接修改存储。
- [ ] 为关键 API 增加集成测试。

验收标准：

- [ ] 可以通过 API 发布异常、注册 Agent、查询任务、回传进展、提交结果、发起审批。
- [ ] `/api/v1/tasks/{task_id}` 返回完整任务详情与进展事件。

### Phase 5：CT Agent 人机交互入口

目标：把 CT Agent 作为 CT 与人的统一入口 / 出口，而不是业务 Agent。

- [ ] 定义结构化命令模型：
  - [ ] `CreateAnomalyEvent`
  - [ ] `RequestTaskStatus`
  - [ ] `ApprovePlan`
  - [ ] `RejectAction`
  - [ ] `RequestProgressSummary`
- [ ] 实现 REST 版 CT Agent message handler。
- [ ] 实现 CLI Demo 入口。
- [ ] 对高风险动作实现“复述计划 -> 等待确认 -> 执行”的流程。
- [ ] CT Agent 查询任务或数据时执行用户角色 / 权限校验。
- [ ] CT Agent 只调用 application service，不直接修改数据库。
- [ ] 补充 CT Agent 命令解析、权限拒绝、高风险确认测试。

验收标准：

- [ ] 人可以通过 CT Agent 发布异常事件。
- [ ] 人可以通过 CT Agent 查询任务状态、当前处理人、耗时和历史进展。
- [ ] 需要审批时，CT Agent 能生成审批请求并提交人的审批决策。

### Phase 6：Data Broker、权限与审计

目标：所有业务 Agent 的数据查询都经由 CT，并可审计、可过滤。

- [ ] 定义通用数据查询请求 / 响应模型。
- [ ] Data Broker 基于 `AgentCard.data_scopes` 和 ACL 校验权限。
- [ ] 支持字段级过滤。
- [ ] 支持实体级过滤。
- [ ] 查询请求、拒绝原因、返回摘要写入审计日志。
- [ ] CT Agent 代表人查询时校验人的角色和权限。
- [ ] 为允许查询、拒绝查询、字段过滤、审计记录补充单元测试。

验收标准：

- [ ] 业务 Agent 不能直接访问 CT 管理的数据源。
- [ ] 无权限查询会被拒绝，并产生带 `trace_id` 的审计记录。

### Phase 7：RabbitMQ 适配器与消息拓扑

目标：用 RabbitMQ 替换内存总线，同时保持核心只依赖 `EventBus` 端口。

- [ ] 新增 RabbitMQ 适配器，核心代码不得导入 RabbitMQ 客户端。
- [ ] 默认 Exchange：`ct.events` topic exchange。
- [ ] 默认 Queue：
  - [ ] `ct.anomalies`，绑定 `anomaly.*`
  - [ ] `ct.tasks`，绑定 `task.*`
  - [ ] `ct.progress`，绑定 `progress.*`
  - [ ] `ct.approvals`，绑定 `approval.*`
  - [ ] `ct.dlq`，用于失败消息和超过重试上限的任务
- [ ] 消息必须携带：
  - [ ] `trace_id`
  - [ ] `event_id` 或 `task_id`
  - [ ] `schema_version`
  - [ ] `occurred_at`
  - [ ] `source`
- [ ] 实现 ack、nack、重试上限、DLQ 发布。
- [ ] 提供 Docker Compose 启动 RabbitMQ。
- [ ] 添加适配器级测试或可跳过的集成测试说明。

验收标准：

- [ ] 使用 RabbitMQ 时，异常、任务、进展、审批事件可以通过配置拓扑流转。
- [ ] 切回内存 EventBus 不需要修改核心用例代码。

### Phase 8：样例业务 Agent 与端到端 Demo

目标：完成第一阶段可演示闭环。

- [ ] 在 `examples/` 中实现样例业务 Agent。
- [ ] 样例 Agent 通过 HTTP Webhook 接收任务。
- [ ] 样例 Agent 至少回传两次进展事件。
- [ ] 样例 Agent 提交最终任务结果。
- [ ] 增加样例异常事件和样例 Policy。
- [ ] 扩展现有 UI 或 CLI，展示任务执行人、耗时、当前阶段、历史进展和结果。
- [ ] 编写端到端 Demo 脚本或 Make / uv 命令。

验收标准：

- [ ] 人通过 CT Agent 或 API 发布异常事件。
- [ ] CT 通过 RabbitMQ 收到事件并匹配 Policy。
- [ ] CT 创建任务并分派给注册业务 Agent。
- [ ] 任务进入 `IN_PROGRESS` 后可查询执行 Agent、耗时和当前阶段。
- [ ] 业务 Agent 至少回传两次进展事件。
- [ ] CT Agent 能把进展反馈给人。
- [ ] 如任务要求审批，CT Agent 能向人确认计划并提交审批结果。
- [ ] 任务完成后，CT 记录结果和完整审计链路。

## 4. 推荐近期优先级

建议下一轮开发优先处理以下事项：

1. **先稳核心模型与状态机**：补齐 `AnomalyEvent`、`ApprovalRequest`、`TaskStateMachine`、审计事件，保证核心无外部依赖。
2. **再做应用服务**：实现异常接收、Policy 匹配、任务创建、进展回传、任务详情查询。
3. **然后补 API**：把应用服务暴露为 `/api/v1/*`，避免 API 层直接操作内存存储。
4. **最后接 RabbitMQ 与样例 Agent**：在核心闭环稳定后接入外部中间件和示例业务。

## 5. 跟踪约定

- 每完成一个功能点，将对应复选框改为 `[x]`。
- 每个 Phase 完成时，应补充：
  - 关键 PR / commit 链接或摘要。
  - 新增 / 修改的主要文件。
  - 运行过的测试命令。
  - 尚未解决的风险和后续 TODO。
- 若某项设计发生变化，应先更新本计划，再落代码，避免 Demo 逐渐偏离“通用框架 / SDK”目标。
