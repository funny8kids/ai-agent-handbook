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
4. **图片**：自制图表统一放 `docs/assets/`（`diagrams/`、`screenshots/`、`covers/`、`icons/` 四类），命名用 `章节-主题.png`（如 `02-agent-basics-agent-loop.png`），先压缩（TinyPNG/Squoosh）再提交；GitBook 编辑器上传的图片默认存放在 `docs/.gitbook/assets/`
5. **链接**：站内链接用相对路径（`../06-memory-rag/rag-basics.md`）；知识点页与资源页保持双向链接

## 提交流程

1. Fork 仓库（或直接在本仓库开分支）
2. 修改内容并自检：文件已在 `SUMMARY.md` 登记、链接可访问、格式符合模板
3. 提交 Pull Request，描述改动内容与原因
4. 维护者审核合并后，GitBook 会自动同步更新

## 风格建议

- 每页聚焦一个主题，宁短勿杂
- 概念首次出现给出中英文对照
- 代码示例尽量可直接运行
- 引用外部资料附原文链接
