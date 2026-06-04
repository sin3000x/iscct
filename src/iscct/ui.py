from __future__ import annotations

from .mock_data import APP_TITLE, MOCK_AGENTS, MOCK_EVENTS, MOCK_PROGRESS, MOCK_TASKS, format_elapsed


def _task_badge_class(status: str) -> str:
    if status == "进行中":
        return "bd-r"
    if status == "等待人工":
        return "bd-e"
    return "bd-k"


def render_home_page() -> str:
    task_cards = []
    for task in MOCK_TASKS:
        task_cards.append(
            f"""
            <div class="tr" id="r-{task['task_id']}" onclick="tog('{task['task_id']}')">
              <div class="trh">
                <span class="tri">{task['task_id']}</span>
                <span class="trt">{task['title']}</span>
                <span class="tra">{task['assignee']}</span>
                <span class="trtm">{format_elapsed(task['started_at']) // 60:02d}:{format_elapsed(task['started_at']) % 60:02d}</span>
                <span class="bdg {_task_badge_class(task['status'])}">{task['status']}</span>
                <span class="chev">▾</span>
              </div>
              <div class="td">
                <div class="steps">
                  <div class="step"><div class="si si-d">✓</div><div class="sbody"><div class="sname">当前阶段</div><div class="smeta">{task['stage']}</div></div></div>
                  <div class="step"><div class="si si-a">↻</div><div class="sbody"><div class="sname">最后进展</div><div class="smeta">{task['last_progress_at'].strftime('%H:%M')}</div></div></div>
                  <div class="step"><div class="si si-p">○</div><div class="sbody"><div class="sname">进度</div><div class="smeta">{task['progress_percent']}%</div></div></div>
                </div>
              </div>
            </div>
            """
        )

    agents_html = "".join(
        f"""
        <div class="agent-card">
          <div class="agent-head">
            <div>
              <div class="agent-name">{agent['display_name']}</div>
              <div class="agent-meta">{agent['agent_id']}</div>
            </div>
            <span class="agent-state {'ok' if agent['status'] == '健康' else 'warm'}">{agent['status']}</span>
          </div>
          <div class="agent-cap">{agent['capability']}</div>
        </div>
        """
        for agent in MOCK_AGENTS
    )

    timeline_html = "".join(
        f"""
        <div class="timeline-item">
          <div class="timeline-stage">{item['stage']}</div>
          <div class="timeline-msg">{item['message']}</div>
        </div>
        """
        for item in MOCK_PROGRESS
    )

    event = MOCK_EVENTS[0]

    return f"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{APP_TITLE}</title>
  <link rel="stylesheet" href="/static/ui.css" />
</head>
<body>
  <div id="cta">
    <div id="hdr">
      <span class="htit">Control Tower</span>
      <span class="hsp"></span>
      <span class="ldot"></span>
      <span class="sp sp-cr">3 严重</span>
      <span class="sp sp-hi">2 高优</span>
      <span class="sp sp-ac">2 处理中</span>
      <span class="hclk" id="clk">--:--:--</span>
    </div>

    <div class="main">
      <aside class="pane side">
        <div class="side-top">
          <div class="side-title">CT Agent</div>
          <div class="side-sub">直接问当前状态、要任务进展、看审批建议。这里先用模拟对话演示人与 CT 的交互。</div>
        </div>
        <div class="chat">
          <div class="chat-stream" id="cmsgs">
            <div class="bubble-row">
              <div class="bubble-label">CT 助手 · 09:30</div>
              <div class="bubble ct">当前共有 <strong>5 个活跃异常</strong>。优先关注 T-2402，因为它在等待审批，窗口期更短。</div>
            </div>
            <div class="bubble-row">
              <div class="bubble-label" style="text-align:right">您 · 09:38</div>
              <div class="bubble user">T-2401 现在卡在哪一步？</div>
            </div>
            <div class="bubble-row">
              <div class="bubble-label">CT 助手 · 09:38</div>
              <div class="bubble ct">卡在备用司机匹配。沪B-67890 和沪C-11111 已就绪，只差沪A-12345 的替代司机到位后就能同批次出发。</div>
            </div>
          </div>
          <div class="chat-input">
            <textarea id="cin" rows="1" placeholder="向 CT 助手询问当前状态或发出指令…" onkeydown="ck(event)"></textarea>
            <button id="csend" onclick="sc()">发送</button>
          </div>
        </div>
      </aside>

      <main class="pane content">
        <div class="summary-grid">
          <div class="summary-card"><div class="summary-num">3</div><div class="summary-label">应发未发</div><div class="summary-sub">松江发货站 · 延误 >40 分</div></div>
          <div class="summary-card"><div class="summary-num">2</div><div class="summary-label">已发未按时到达</div><div class="summary-sub">预测延误 35 分钟</div></div>
          <div class="summary-card"><div class="summary-num">1</div><div class="summary-label">今日已解决</div><div class="summary-sub">平均处置 28 分钟</div></div>
        </div>

        <section>
          <div class="section">活跃任务 <span>点击展开 SAGA 执行步骤</span></div>
          {''.join(task_cards)}
        </section>

        <section>
          <div class="section">在线 Agent <span>模拟数据</span></div>
          <div class="agents">{agents_html}</div>
        </section>

        <section>
          <div class="section">最新异常 <span>{event['event_type']}</span></div>
          <div class="summary-card">
            <div class="summary-label">{event['severity']}</div>
            <div class="summary-sub">{event['summary']}</div>
          </div>
        </section>

        <section>
          <div class="section">最近进展 <span>timeline</span></div>
          <div class="timeline">{timeline_html}</div>
        </section>
      </main>
    </div>
  </div>

  <script src="/static/ui.js"></script>
</body>
</html>
"""
