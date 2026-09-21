# 真实产品 UI 截图清单 (MANIFEST)

> 本目录收录 AI Agent 相关工具的**真实产品界面截图**（非手绘示意图、非营销大图），
> 全部为无 Cookie 横幅、无遮罩弹窗的干净界面，供正文配图引用。
> 采集/访问日期统一为 **2026-09-22**。

| filename | tool | 一句话说明（这张图讲什么） | source URL | 访问日期 | 接入位置 |
| --- | --- | --- | --- | --- | --- |
| `01-langfuse-trace-ui.png` | Langfuse | Trace 列表 + Span 瀑布流 + 单步 Input/Output 详情，展示一次 Agent 调用链的可观测视图 | https://langfuse.com/images/docs/tracing-overview.png （来自 https://langfuse.com/docs/tracing ） | 2026-09-22 | `docs/11-engineering/observability-tools.md` |
| `02-mcp-inspector-ui.png` | MCP Inspector | Web 版 Inspector 窗口：左侧 Tools 列表、中间 Results、右侧 Messages 协议监控面板 | https://mintcdn.com/mcp/gk28X8wi_tbRYzej/images/inspector/web-monitor-sidebar.png （来自 https://modelcontextprotocol.io/docs/tools/inspector ） | 2026-09-22 | `docs/05-tool-protocol/mcp.md` |
| `03-openhands-automate-ui.png` | OpenHands | 编码 Agent 平台的 Automate 视图：会话侧栏 + 自动化任务卡片 + 工作流模板 | https://assets.openhands.dev/screenshot/automation-preview.png （来自 OpenHands 仓库 README） | 2026-09-22 | `docs/12-applications/coding-agent.md`、`docs/13-resources/projects/openhands.md` |
| `04-dify-workflow-ui.png` | Dify | 工作流编排画布：START→LLM→LLM 节点连线 + 右侧 LLM 节点配置面板（模型/上下文/系统提示词） | https://assets-docs.dify.ai/dify-enterprise-mintlify/en/guides/workflow/node/5aefed96962bd994f8f05bac96b11e22.png （来自 https://docs.dify.ai/en/guides/workflow/node/llm ） | 2026-09-22 | `docs/09-frameworks/README.md` |
| `05-openwebui-chat-ui.png` | Open WebUI | 自托管对话界面：模型选择 + 对话流 + 内联渲染的图表/表格 + 右侧 Artifacts 工作区 | https://docs.openwebui.com/images/landing/hero.png （来自 https://docs.openwebui.com ） | 2026-09-22 | `docs/12-applications/general-agent-products.md` |
| `06-arize-phoenix-trace-ui.png` | Arize Phoenix | Trace Details：左侧 Span 树/瀑布流 + 右侧选中 Span 的 Prompt/Output 与延迟、Tokens 指标 | https://storage.googleapis.com/arize-phoenix-assets/assets/images/phoenix-docs-images/15fe0366-image.jpeg （来自 https://arize.com/docs/phoenix/tracing/llm-traces ） | 2026-09-22 | `docs/11-engineering/logging-tracing-monitoring.md` |
| `07-autogen-studio-ui.png` | AutoGen Studio | Team Builder 可视化多智能体编排：组件库（Agents/Models/Tools/Terminations）+ 节点连线画布 | https://media.githubusercontent.com/media/microsoft/autogen/refs/heads/main/python/packages/autogen-studio/docs/ags_screen.png （来自 microsoft/autogen README） | 2026-09-22 | `docs/09-frameworks/autogen.md` |
| `08-langsmith-experiment-ui.png` | LangSmith | 实验对比表：逐用例并排多个评估器得分（Hallucination/Helpful/Random）+ 延迟 + Tokens，Heat Map 染色 | https://mintcdn.com/langchain-5e9cc07a/0B2PFrFBMRWNccee/langsmith/images/experiment-view.png （来自 https://docs.smith.langchain.com/evaluation ） | 2026-09-22 | `docs/10-evaluation-safety/evaluation-metrics.md` |

## 采集方法说明
- 使用 Edge `--headless=new` 渲染目标文档/产品页；对 Mintlify/文档站中**内嵌的产品截图**，
  通过 `--dump-dom` 拿到其原生高清图 URL 后直接下载，再裁剪/缩放至正文宽度（约 1000–1280px），
  从而得到无导航栏、无 Cookie 横幅的干净界面。
- 所有图片已统一转为 PNG，`optimize=True` 压缩。
- 2026-09-22 复核：上表 7 个来源 URL 逐个 `curl -L` 均返回 HTTP 200（正文页与图片资源皆然）；
  `08` 的两个 LangSmith mintcdn 地址由 `docs.smith.langchain.com/evaluation` 渲染结果中提取。
- 逐张目检：8 张全部为真实产品 UI（能辨认出具体面板与文字），无 cookie 横幅、无遮罩、无纯营销大图。

## 未能干净采集的工具（已放弃，正文改用自绘图/Mermaid）
- **LangGraph Studio**：`docs.langchain.com` / `docs.smith.langchain.com` 的 Studio 页面为客户端渲染，
  渲染后 DOM 内只有品牌图（`langchain-docs-*.png`），无公开可用的产品界面截图。
- **browser-use**：`docs.browser-use.com` 全站（含 quickstart、cloud 指南）未内嵌任何产品截图，
  其真实「Agent 驱动浏览器 + 动作浮层」界面需实际运行才能捕获。
- **CrewAI**：文档站 `crews.png` / `flows.png` 经目检是**概念示意图而非产品界面**，与本书自绘 Mermaid 等价，
  故不引入；AutoGen Studio 一张已足够代表「可视化编排团队」这一形态。
- **Langfuse Cloud Demo**（`cloud.langfuse.com/project/.../traces`）：官方 demo 工作区跳转登录后墙，
  headless 捕获到的是 Sign in 页，故改用其文档内嵌截图。
