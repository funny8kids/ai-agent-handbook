---
tags: [tooling]
type: knowledge
status: published
updated: 2026-09-10
---

# 浏览器、代码、文件系统工具

> **一句话**：这三类工具覆盖 Agent 90% 的实际工作面——读网页、跑代码、动文件；各自的安全与设计要点完全不同。
> **难度**：进阶
> **标签**：`#tooling`

## 先看结论

- 文件系统工具：最小集是 read / write / edit / glob / grep——Pi 证明四个原子工具就够干活
- 代码执行工具：能力最强、风险最高，必须沙箱化；结果回填要截断
- 浏览器工具：分「API 型」（fetch/search）与「GUI 型」（Playwright 操作页面），成本与适用场景不同

## 三类工具设计要点

| 工具类 | 关键设计 | 主要风险 | 必配防线 |
|---|---|---|---|
| 文件系统 | edit 用「旧文匹配→替换」防覆盖；路径校验 | 误删、越权读写 | 工作目录白名单、只读区 |
| 代码执行 | 超时、内存上限、无网络默认 | 任意代码执行、资源耗尽 | 沙箱（容器/microVM）、egress 白名单 |
| 浏览器 | 等待策略、DOM 精简提取 | 网页内容注入恶意指令 | 内容当数据不当指令、域名白名单 |

## 文件编辑的安全模式

```python
def edit_file(path, old_text, new_text):
    content = read(path)
    if content.count(old_text) != 1:
        return "错误：匹配 0 或多处，请提供更长的上下文片段"  # 防误伤
    write(path, content.replace(old_text, new_text))
    return "已修改，修改后片段预览：" + preview(new_text)
```

「旧文匹配替换」是 Claude Code Edit 工具与 Pi edit 工具的共同设计：强迫模型先读后改、精确锚定，杜绝「幻觉覆盖」。

## 源码案例

- **Pi 的四工具极简主义**（[earendil-works/pi](https://github.com/earendil-works/pi)）：read/write/edit/bash 覆盖全部文件与执行需求——grep 藏在 bash 里（`rg`）、glob 也是。启示：工具集大小与能力无关，与模型选择难度有关
- **Claude Code 的代码执行权衡**（逆向分析）：Codex/Claude Code 类产品把 Bash 当「万能逃生舱」，但系统提示词明确优先专用工具（安全审计、权限粒度都更细）；输出截断规则（如 30000 字符）硬编码在工具层
- **DeepSeek Harness 的沙箱执行**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：代码执行默认进 landlock-run 沙箱，网络与文件访问按 profile 配置——「执行类工具默认危险」是架构级共识
- **浏览器工具生态**：[Playwright MCP](https://github.com/microsoft/playwright-mcp)（微软官方，结构化 DOM 快照而非截图，token 省 10 倍+）、[browser-use](https://github.com/browser-use/browser-use)（视觉+DOM 混合，开源 GUI 自动化标配）

## 常见误区

- ❌ 浏览器工具 = Playwright 全家桶搬进来：GUI 操作贵且脆，能用 API/fetch 解决的别点鼠标
- ❌ 代码执行沙箱只限文件：Python 可以读环境变量、发网络请求——秘钥泄漏路径主要在这
- ❌ 工具结果全量回填：网页抓取动辄几十万 token，先提取正文/相关片段再回填

## 小练习

设计「竞品价格监控」Agent：用 API 型还是 GUI 型浏览器工具？价格页结构变化时如何兜底？每天跑批的沙箱预算怎么定？

## 相关知识点

- [工具权限与沙箱](tool-permission-sandbox.md)
- [Computer Use / Browser Use](computer-use-browser-use.md)
