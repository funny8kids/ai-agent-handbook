# 知识点模板

> 新增知识点页面时，先按 [风格指南](style-guide.md) 第三节选定体裁，再复制对应模板。
> **不要**把下面的小节当成打卡清单：与主题无关的小节直接删掉。

## 使用说明

1. 选体裁：A 原理型 / B 概念型 / C 实战型（见 [风格指南](style-guide.md) 第三节）
2. 复制对应「模板正文」到新页面（如 `02-agent-basics/xxx.md`）
3. 填好 frontmatter（`tags` / `type` / `status` / `updated`）
4. 在 `docs/SUMMARY.md` 中登记该页面
5. 自检通过 [风格指南](style-guide.md) 第九节检查清单后，才把 `status` 改为 `published`

## 通用 frontmatter

```yaml
---
tags: [agent, basics, beginner]
type: knowledge
status: draft
updated: 2026-09-10
---
```

| 字段 | 说明 | 取值 |
|---|---|---|
| `tags` | 小写英文短标签，2–5 个 | `agent`、`llm`、`rag`、`mcp`、`multi-agent`、`evaluation`、`safety`、`framework`、`tooling` |
| `type` | 页面类型 | `knowledge` / `resource` / `index` |
| `status` | 写作状态 | `draft`（编写中）/ `reviewing`（待审）/ `published`（已达标） |
| `updated` | 最后更新日期 | `YYYY-MM-DD` |

---

## A. 原理型模板（讲"为什么/怎么算"）

````markdown
---
tags: [llm, basics]
type: knowledge
status: draft
updated: 2026-09-10
---

# 【原理名称】

> **一句话**：用一句话说清它解决什么问题、核心机制是什么。

## 问题动机

没有它会遇到什么麻烦？先给场景，再给定义。

## 核心机制

给出公式、推导或伪代码。以注意力为例：

$$
\mathrm{Attention}(Q,K,V)=\mathrm{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right)V
$$

逐项解释：

- $QK^\top$：查询与键的点积，衡量"每个词该关注谁"
- $\sqrt{d_k}$：缩放因子，防止点积随维度增大而方差膨胀、softmax 饱和
- $V$：按权重加权求和，得到输出

（伪代码须显式标注为伪代码，不要与真实代码混用。）

```text
# 伪代码：单头注意力前向
scores = Q @ K.T / sqrt(d_k)
weights = softmax(scores)
output = weights @ V
```

## 直觉解释

机制讲完后，再用一个日常类比巩固（类比不能替代上面的公式）。

## 工程含义

这个原理对构建 Agent 意味着什么？（成本、上下文、选型等）

## 参考资料

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [官方文档/源码链接](https://example.com)

## 相关知识点

- [相关概念](./相对路径.md)
````

---

## B. 概念型模板（讲"是什么/和什么不同"）

````markdown
---
tags: [agent, basics, beginner]
type: knowledge
status: draft
updated: 2026-09-10
---

# 【概念名称】

> **一句话**：定义 + 边界，一句话说清。

## 定义与边界

- 什么算：……
- 什么不算：……

## 与相邻概念的对比

| 概念 | 关键差异 | 典型场景 |
|---|---|---|
| A | …… | …… |
| B | …… | …… |

## 一个具体例子

用一个真实场景说明，避免抽象。

## 参考资料

- [一手来源](https://example.com)

## 相关知识点

- [相关概念](./相对路径.md)
````

---

## C. 实战型模板（讲"怎么做"）

````markdown
---
tags: [tooling, engineering]
type: knowledge
status: draft
updated: 2026-09-10
---

# 【实践名称】

> **一句话**：这个做法解决什么问题、适用于什么场景。

## 适用场景与前置条件

- 什么时候用：……
- 前置要求：……

## 可运行示例

真实依赖、真实函数签名：

```python
from openai import OpenAI

client = OpenAI()
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "你好"}],
)
print(resp.choices[0].message.content)
```

## 常见故障与排查

| 现象 | 原因 | 处理 |
|---|---|---|
| …… | …… | …… |

## 参考资料

- [官方文档](https://example.com)

## 相关知识点

- [相关概念](./相对路径.md)
````

## 写作检查清单

详见 [风格指南](style-guide.md) 第九节。核心几条：

- [ ] 体裁明确，结构符合体裁，没有硬凑小节
- [ ] 页面 emoji ≤1（标题），二级标题与正文无 emoji
- [ ] 原理型给出了核心公式并解释每一项
- [ ] 每个数字都能点到一手来源，文末有「参考资料」
- [ ] 至少 1 张 Mermaid 或自绘 SVG 配图
- [ ] 案例与主题相关，没有硬塞无关项目
- [ ] 达到对应体裁的字数下限
- [ ] 文件名英文小写 + 连字符，已在 `SUMMARY.md` 登记
