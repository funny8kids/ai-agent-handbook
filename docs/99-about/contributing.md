---
tags: [meta, contributing]
type: index
status: published
updated: 2026-09-22
---

# 贡献指南

欢迎参与共建这本 AI Agent 手册！请按以下流程贡献内容。

## 贡献方式

- **补充/修订知识点**：在对应章节页面撰写或修改内容
- **新增资源**：向 [13 资源库](../13-resources/README.md) 添加论文、课程、项目、工具等
- **纠错**：修正过时表述、失效链接

## 写作规范

1. **文件命名**：英文小写 + 连字符，如 `what-is-agent.md`；标题用中文
2. **使用模板**：
   - 知识点页面 → [知识点模板](../14-templates/knowledge-template.md)
   - 资源页面 → [资源模板](../14-templates/resource-template.md)
   - 行文风格（emoji、图示、类比、提示块）→ [风格指南](../14-templates/style-guide.md)
3. **目录登记**：新增页面必须在 `docs/SUMMARY.md` 中登记，否则不会出现在 GitBook 目录
4. **图片**：**所有图片统一放 `docs/.gitbook/assets/`**——这是 GitBook 的资源目录，只有放在这里的图片才会被 GitBook 导入并提供访问；放在其他目录（如自建的 `docs/assets/`）在 GitBook 上会加载失败。命名用 `章节-主题.svg`（如 `16-continuous-batching.svg`）或 `章节-主题.png`，截图先压缩（TinyPNG/Squoosh）再提交；矢量图（含动画）写法与限制见 [风格指南 · 需要「会动」的图用 SVG](../14-templates/style-guide.md)
5. **链接**：站内链接用相对路径（`../06-memory-rag/rag-basics.md`）；知识点页与资源页保持双向链接

## 提交流程

1. Fork 仓库（或直接在本仓库开分支）
2. 修改内容并自检：文件已在 `SUMMARY.md` 登记、链接可访问、格式符合模板
3. 提交 Pull Request，描述改动内容与原因
4. 维护者审核合并后，GitBook 会自动同步更新

## 图文与排版规范

- **导语用 hint 块**：每篇知识点页开头用 `{% hint style="info" %}` 放「一句话」结论；易踩的坑用 `style="tip"` / `"warning"`，危险操作警示用 `"danger"`
- **正文流程图用 Mermaid**：GitBook 原生渲染 ```` ```mermaid ```` 块，无需插件；节点 ≤12 个，中文标签加引号，`flowchart` 画结构、`sequenceDiagram` 画交互时序
- **章首总览图**：每章导读配一张全局地图（现有 20+ 张 SVG 在 `docs/.gitbook/assets/`，新章优先沿用同风格）
- **长推导可折叠**：多步数学推导放正文，超一屏的证明用 `{% expandable %}` 收起，主页只留结论
- **每页一图起步**：核心机制一节至少配一张能「看图回忆结论」的图；图要为解释而画，不放装饰图

## 快速上手（good first page）

- 给还没有配图的知识点页补一张 Mermaid 图（用 `grep -L mermaid docs/*/*.md` 找缺口）
- 给 [开源项目索引](../13-resources/projects/README.md) 补一个你实测过的项目并写「一句话点评」
- 校对任意一页的失效链接与过时数字（star 数、版本号、日期）

## 风格建议

- 每页聚焦一个主题，宁短勿杂
- 概念首次出现给出中英文对照
- 代码示例尽量可直接运行
- 引用外部资料附原文链接

## 授权与复用

提交即表示同意正文与图示按本书的开源条款发布，具体授权范围与引用规范见 [许可证](license.md)。
