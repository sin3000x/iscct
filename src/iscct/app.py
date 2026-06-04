from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .mock_data import (
    APP_SUBTITLE,
    APP_TITLE,
    MOCK_AGENTS,
    MOCK_EVENTS,
    MOCK_PROGRESS,
    MOCK_TASKS,
    format_elapsed,
)

app = FastAPI(title=APP_TITLE)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    task_cards = []
    for task in MOCK_TASKS:
        task_cards.append(
            f"""
            <article class=\"card task\">
              <div class=\"row\">
                <h3>{task['title']}</h3>
                <span class=\"badge\">{task['status']}</span>
              </div>
              <p><strong>Assignee</strong> {task['assignee']}</p>
              <p><strong>Stage</strong> {task['stage']}</p>
              <p><strong>Elapsed</strong> {format_elapsed(task['started_at'])}s</p>
              <div class=\"bar\"><span style=\"width: {task['progress_percent']}%\"></span></div>
            </article>
            """
        )

    agent_cards = []
    for agent in MOCK_AGENTS:
        agent_cards.append(
            f"""
            <article class=\"card\">
              <h3>{agent['display_name']}</h3>
              <p><strong>Status</strong> {agent['status']}</p>
              <p>{agent['capability']}</p>
            </article>
            """
        )

    event = MOCK_EVENTS[0]
    progress_items = []
    for item in MOCK_PROGRESS:
        progress_items.append(f"<li><strong>{item['stage']}</strong> — {item['message']}</li>")

    return f"""
    <!doctype html>
    <html lang=\"en\">
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>{APP_TITLE}</title>
        <style>
          :root {{ color-scheme: dark; }}
          body {{ margin: 0; font-family: Inter, system-ui, sans-serif; background: #0b1020; color: #e5e7eb; }}
          .shell {{ max-width: 1200px; margin: 0 auto; padding: 40px 24px 56px; }}
          .hero {{ display: grid; gap: 12px; margin-bottom: 28px; }}
          .hero h1 {{ margin: 0; font-size: 40px; }}
          .hero p {{ margin: 0; color: #94a3b8; max-width: 780px; }}
          .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}
          .section {{ margin-top: 24px; }}
          .section h2 {{ margin: 0 0 12px; font-size: 20px; }}
          .card {{ background: rgba(15, 23, 42, 0.92); border: 1px solid rgba(148, 163, 184, 0.18); border-radius: 18px; padding: 18px; box-shadow: 0 16px 40px rgba(0, 0, 0, 0.25); }}
          .card h3 {{ margin: 0 0 10px; }}
          .card p {{ margin: 8px 0; color: #cbd5e1; }}
          .row {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; }}
          .badge {{ background: #1d4ed8; color: white; border-radius: 999px; padding: 6px 10px; font-size: 12px; }}
          .bar {{ height: 8px; background: rgba(148, 163, 184, 0.18); border-radius: 999px; overflow: hidden; margin-top: 14px; }}
          .bar span {{ display: block; height: 100%; background: linear-gradient(90deg, #22c55e, #60a5fa); }}
          ul {{ margin: 0; padding-left: 18px; color: #cbd5e1; }}
          .hero-actions {{ display: flex; gap: 12px; flex-wrap: wrap; }}
          .button {{ display: inline-block; padding: 10px 14px; border-radius: 12px; text-decoration: none; color: white; background: #2563eb; }}
          .muted {{ color: #94a3b8; }}
        </style>
      </head>
      <body>
        <main class=\"shell\">
          <section class=\"hero\">
            <div class=\"badge\">Hello World front desk</div>
            <h1>{APP_TITLE}</h1>
            <p>{APP_SUBTITLE}. This mock dashboard shows what a person sees first: active tasks, current agents, the latest anomaly, and live progress updates.</p>
            <div class=\"hero-actions\">
              <a class=\"button\" href=\"/api/health\">Open health check</a>
              <span class=\"muted\">All data here is mock data for now.</span>
            </div>
          </section>

          <section class=\"section\">
            <h2>What the front desk sees first</h2>
            <div class=\"grid\">{''.join(task_cards)}</div>
          </section>

          <section class=\"section\">
            <h2>Agents online</h2>
            <div class=\"grid\">{''.join(agent_cards)}</div>
          </section>

          <section class=\"section\">
            <h2>Latest anomaly</h2>
            <article class=\"card\">
              <p><strong>{event['event_type']}</strong> · {event['severity']}</p>
              <p>{event['summary']}</p>
              <p class=\"muted\">Source: {event['source']}</p>
            </article>
          </section>

          <section class=\"section\">
            <h2>Recent progress timeline</h2>
            <article class=\"card\">
              <ul>{''.join(progress_items)}</ul>
            </article>
          </section>
        </main>
      </body>
    </html>
    """


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "mock"}
