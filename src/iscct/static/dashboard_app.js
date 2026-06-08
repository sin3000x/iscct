import { ChatBubble } from './chat_bubble.js';
import { TaskCard } from './task_card.js';

const { createApp, nextTick } = Vue;

const bootstrap = window.__ISCCT_BOOTSTRAP__ || {};
const appTitle = bootstrap.appTitle || '控制塔演示';
const appSubtitle = bootstrap.appSubtitle || '面向人工的一线 CT 运营工作台';
const clockPad = (n) => String(n).padStart(2, '0');
const toTimestamp = (dateLike) => {
  const d = new Date(dateLike);
  return `${clockPad(d.getHours())}:${clockPad(d.getMinutes())}`;
};
const durationText = (startedAt) => {
  const diff = Math.max(Date.now() - new Date(startedAt).getTime(), 0);
  const mins = Math.floor(diff / 60000);
  const secs = Math.floor((diff % 60000) / 1000);
  return `${clockPad(mins)}:${clockPad(secs)}`;
};

createApp({
  components: { ChatBubble, TaskCard },
  data() {
    return {
      appTitle,
      appSubtitle,
      clock: '--:--:--',
      draft: '',
      chatMode: '在线',
      expandedTaskId: bootstrap.tasks?.[0]?.task_id || null,
      messages: [
        { role: 'ct', author: 'CT 助手', time: '09:30', html: '当前共有 <strong>5 个活跃异常</strong>，需关注两类情况：<br><br>① 松江发货站 <strong>3 辆应发未发</strong>，计划 09:00 出发，已延误超 40 分钟，T-2401 处理中（正在匹配备用司机）<br>② 沪D-22222 <strong>在途延误 35 分钟</strong>，路由优化 Agent 已备好绕行方案，<strong>T-2402 等待您审批</strong><br><br>建议优先处理 T-2402，车辆正在行驶，绕行窗口期有限。' },
        { role: 'user', author: '您', time: '09:38', html: 'T-2401 里，除了司机失联那辆，另外两辆现在什么状态？' },
        { role: 'ct', author: 'CT 助手', time: '09:38', html: '沪B-67890 和沪C-11111 均已就绪：货物装载完毕、司机在岗、车检通过，处于「等待同批次出发」状态。<br><br>阻塞点仅在沪A-12345 的备用司机匹配，匹配完成后三辆车将同批次出发，预计 5 分钟内有结果。' },
      ],
      tasks: (bootstrap.tasks || []).map((task) => ({
        ...task,
        startedAtText: durationText(task.started_at),
        lastProgressText: toTimestamp(task.last_progress_at),
        steps: [
          { name: '当前阶段', meta: task.stage, note: task.status === '等待人工' ? '需要人工审批后继续' : '状态机正在推进中', icon: task.status === '已完成' ? '✓' : task.status === '等待人工' ? '⏸' : '↻', stateClass: task.status === '已完成' ? 'step-ok' : task.status === '等待人工' ? 'step-warn' : 'step-info' },
          { name: '最后进展', meta: task.lastProgressText, note: '最近一次回传已写入审计链路', icon: '↻', stateClass: 'step-info' },
          { name: '进度', meta: `${task.progress_percent}%`, note: '进度值来自任务状态机', icon: '○', stateClass: 'step-neutral' },
        ],
      })),
      agents: bootstrap.agents || [],
      progress: (bootstrap.progress || []).map((item) => ({ ...item, occurredText: toTimestamp(item.occurred_at) })),
      event: bootstrap.event || {},
    };
  },
  computed: {
    summary() {
      return { severe: 3, high: 2, active: this.tasks.filter((task) => task.status === '进行中' || task.status === '等待人工').length };
    },
    summaries() {
      return [
        { value: 3, label: '应发未发', note: '松江发货站 · 延误 >40 分' },
        { value: 2, label: '已发未达', note: '预测延误 35 分钟' },
        { value: 1, label: '今日已解决', note: '平均处置 28 分钟' },
      ];
    },
  },
  mounted() {
    this.updateClock();
    this.clockTimer = window.setInterval(() => this.updateClock(), 1000);
    nextTick(() => this.scrollChatToEnd());
  },
  beforeUnmount() {
    window.clearInterval(this.clockTimer);
  },
  methods: {
    updateClock() {
      const d = new Date();
      this.clock = [d.getHours(), d.getMinutes(), d.getSeconds()].map(clockPad).join(':');
    },
    scrollChatToEnd() {
      const el = this.$refs.chatStream;
      if (el) el.scrollTop = el.scrollHeight;
    },
    toggleTask(taskId) {
      this.expandedTaskId = this.expandedTaskId === taskId ? null : taskId;
    },
    badgeClass(status) {
      return { 'bd-r': status === '进行中', 'bd-e': status === '等待人工', 'bd-k': status === '已完成' };
    },
    addMessage(role, text) {
      const now = new Date();
      this.messages.push({ role, author: role === 'ct' ? 'CT 助手' : '您', time: [now.getHours(), now.getMinutes()].map(clockPad).join(':'), html: text });
      nextTick(() => this.scrollChatToEnd());
    },
    sendMessage() {
      const text = this.draft.trim();
      if (!text) return;
      this.draft = '';
      this.addMessage('user', text);
      window.setTimeout(() => {
        this.addMessage('ct', '收到。这里是 Vue 版 mock CT 助手视图，后续可继续接入真实任务查询、审批流和 CT Agent。');
      }, 450);
    },
    formatDuration(startedAt) {
      return durationText(startedAt);
    },
  },
  template: `
    <div>
      <header class="topbar">
        <div>
          <div class="brand-kicker">Control Tower Demo</div>
          <h1 class="brand-title">{{ appTitle }}</h1>
          <p class="brand-sub">{{ appSubtitle }}</p>
        </div>
        <div class="topbar-metrics">
          <span class="metric danger">{{ summary.severe }} 严重</span>
          <span class="metric warn">{{ summary.high }} 高优</span>
          <span class="metric info">{{ summary.active }} 处理中</span>
          <span class="clock">{{ clock }}</span>
        </div>
      </header>

      <main class="layout">
        <aside class="panel chat-panel">
          <div class="panel-head">
            <div>
              <div class="panel-title">CT Agent</div>
              <div class="panel-sub">支持自然语言问答、查询任务状态和发起人工确认。</div>
            </div>
            <span class="pill">{{ chatMode }}</span>
          </div>

          <div class="chat-stream" ref="chatStream">
            <ChatBubble v-for="(msg, idx) in messages" :key="idx" :message="msg" />
          </div>

          <div class="chat-input">
            <textarea v-model="draft" rows="2" placeholder="向 CT 助手询问当前状态，或输入要发起的命令..." @keydown.enter.exact.prevent="sendMessage"></textarea>
            <button @click="sendMessage">发送</button>
          </div>
        </aside>

        <section class="content">
          <section class="summary-grid">
            <article class="summary-card" v-for="item in summaries" :key="item.label">
              <div class="summary-num">{{ item.value }}</div>
              <div class="summary-label">{{ item.label }}</div>
              <div class="summary-sub">{{ item.note }}</div>
            </article>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <div class="panel-title">活跃任务</div>
                <div class="panel-sub">点击卡片展开状态机、当前阶段和最近进展。</div>
              </div>
              <span class="pill">{{ tasks.length }} 条</span>
            </div>

            <div class="task-list">
              <TaskCard v-for="task in tasks" :key="task.task_id" :task="task" :expanded="expandedTaskId === task.task_id" :badgeClass="badgeClass" :toggleTask="toggleTask" :formatDuration="formatDuration" />
            </div>
          </section>

          <section class="grid-2">
            <div class="panel">
              <div class="panel-head">
                <div>
                  <div class="panel-title">在线 Agent</div>
                  <div class="panel-sub">展示注册状态、能力和基本健康度。</div>
                </div>
              </div>
              <div class="agent-grid">
                <article v-for="agent in agents" :key="agent.agent_id" class="agent-card">
                  <div class="agent-head">
                    <div>
                      <div class="agent-name">{{ agent.display_name }}</div>
                      <div class="agent-meta">{{ agent.agent_id }}</div>
                    </div>
                    <span class="agent-state" :class="agent.status === '健康' ? 'ok' : 'warm'">{{ agent.status }}</span>
                  </div>
                  <div class="agent-cap">{{ agent.capability }}</div>
                </article>
              </div>
            </div>

            <div class="panel">
              <div class="panel-head">
                <div>
                  <div class="panel-title">最近进展</div>
                  <div class="panel-sub">业务 Agent、CT Agent 与系统调度器的进展回传。</div>
                </div>
              </div>
              <div class="timeline">
                <article v-for="item in progress" :key="item.stage + item.message" class="timeline-item">
                  <div class="timeline-stage">{{ item.stage }}</div>
                  <div class="timeline-msg">{{ item.message }}</div>
                </article>
              </div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <div class="panel-title">最新异常</div>
                <div class="panel-sub">{{ event.event_type }}</div>
              </div>
              <span class="pill">{{ event.severity }}</span>
            </div>
            <div class="event-card">
              <div class="event-summary">{{ event.summary }}</div>
              <div class="event-meta">{{ event.source }} · {{ event.trace_id || event.event_id || '—' }}</div>
            </div>
          </section>
        </section>
      </main>
    </div>
  `,
}).mount('#app');
