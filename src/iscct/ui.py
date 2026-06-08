from __future__ import annotations

from string import Template

from .mock_data import APP_TITLE, APP_SUBTITLE, MOCK_AGENTS, MOCK_EVENTS, MOCK_PROGRESS, MOCK_TASKS


PAGE_TEMPLATE = Template(
    """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>$APP_TITLE</title>
  <link rel="stylesheet" href="/static/ui.css" />
  <script defer src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
  <script type="module" defer src="/static/dashboard_app.js"></script>
</head>
<body>
  <div id="app" v-cloak></div>

  <script>
    window.__ISCCT_BOOTSTRAP__ = {
      appTitle: $APP_TITLE_LITERAL,
      appSubtitle: $APP_SUBTITLE_LITERAL,
      tasks: $MOCK_TASKS_LITERAL,
      agents: $MOCK_AGENTS_LITERAL,
      progress: $MOCK_PROGRESS_LITERAL,
      event: $MOCK_EVENT_LITERAL,
    }
  </script>
</body>
</html>
"""
)


def render_home_page() -> str:
    """渲染首页 HTML。

    :return: 包含前端启动所需静态模板与 mock 数据的 HTML 字符串。
    """
    return PAGE_TEMPLATE.substitute(
        APP_TITLE=APP_TITLE,
        APP_TITLE_LITERAL=repr(APP_TITLE),
        APP_SUBTITLE_LITERAL=repr(APP_SUBTITLE),
        MOCK_TASKS_LITERAL=repr(MOCK_TASKS),
        MOCK_AGENTS_LITERAL=repr(MOCK_AGENTS),
        MOCK_PROGRESS_LITERAL=repr(MOCK_PROGRESS),
        MOCK_EVENT_LITERAL=repr(MOCK_EVENTS[0]),
    )
