---
tags: [meta, template]
type: index
status: published
updated: 2026-09-23
---

# 知识点模板

> 新增知识点页面时，先按 [风格指南](style-guide.md) 第三节选定体裁，再复制对应模板。
> **不要**把下面的小节当成打卡清单：与主题无关的小节直接删掉。

## 使用说明

1. 选体裁：A 原理型 / B 概念型 / C 实战型（见 [风格指南](style-guide.md) 第三节）
2. 复制对应「模板正文」到新页面（如 `02-agent-basics/xxx.md`）
3. 填好 frontmatter（`tags` / `type` / `status` / `updated`）——`updated` 写**当天日期**，之后每次改正文都要同步（口径见 [风格指南](style-guide.md) 第八节）
4. 在 `docs/SUMMARY.md` 中登记该页面
5. 自检通过 [风格指南](style-guide.md) 第九节检查清单后，才把 `status` 改为 `published`

## 通用 frontmatter

```yaml
---
tags: [agent, basics, beginner]
type: knowledge
status: draft
updated: 2026-09-20
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

{% hint style="info" %}
**一句话**：用一句话说清它解决什么问题、核心机制是什么。
{% endhint %}

## 问题动机

没有它会遇到什么麻烦？先给场景，再给定义。

## 核心机制

给出公式与推导，并用**形状契约**说明每一步的输入输出规模（写伪代码不如把形状写对——形状错了，读者一眼就能看出来）：

$$
\mathrm{Attention}(Q,K,V)=\mathrm{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right)V
$$

逐项解释：

- $$QK^\top$$：查询与键的点积，衡量"每个词该关注谁"
- $$\sqrt{d_k}$$：缩放因子，防止点积随维度增大而方差膨胀、softmax 饱和
- $$V$$：按权重加权求和，得到输出

```json
{
  "Q": "[n_seq, d_k]",
  "K": "[n_seq, d_k]",
  "scores": "[n_seq, n_seq]  ← 平方膨胀发生在这一行",
  "weights": "softmax 后每行和为 1",
  "output": "[n_seq, d_k]  ← 与 Q 同形，所以能堆层"
}
```

三句话读完这张表：序列长度 $$n_{seq}$$ 让 `scores` 按平方增长（这就是长上下文贵的地方），归一化让注意力是"分配"而不是"叠加"，输出恒等于 `Q` 的形状（所以残差连接才接得上）。

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

{% hint style="info" %}
**一句话**：定义 + 边界，一句话说清。
{% endhint %}

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

{% hint style="info" %}
**一句话**：这个做法解决什么问题、适用于什么场景。
{% endhint %}

## 适用场景与前置条件

- 什么时候用：……
- 前置要求：……

## 数据契约与逐步演示

先给一段**字段名属实**的请求契约（读者照着能在自己 SDK 里对上号）：

```json
{
  "model": "gpt-4o-mini",
  "messages": [{ "role": "user", "content": "你好" }],
  "max_output_tokens": 256,
  "temperature": 0
}
```

再点明返回值里该读哪一个字段，别让人去猜整个响应对象：正文在 `choices[0].message.content`，工具调用意图在同级的 `tool_calls`，用量与计费在 `usage.total_tokens`，出错了看状态码 + `error.code` 而不是看 body 长度。

多步过程用 `{% stepper %}` 展开，读者可以一步步点着看：

{% stepper %}
{% step %}组装请求：系统提示 + 历史 + 本轮输入按契约字段拼好，先估 token 再发{% endstep %}
{% step %}读回 `content`，若同时有 `tool_calls` 则本轮不结束，先执行工具{% endstep %}
{% step %}把工具结果作为新消息追加回去，回到上一步直到没有 `tool_calls`{% endstep %}
{% endstepper %}

分支结局用 `{% tabs %}` 并列，避免写成"可能会失败"：

{% tabs %}
{% tab title="正常结束" %}`finish_reason = "stop"`，无 `tool_calls`{% endtab %}
{% tab title="被截断" %}`finish_reason = "length"`——说明 `max_output_tokens` 给小了，或该走流式{% endtab %}
{% tab title="要调工具" %}`finish_reason = "tool_calls"`，参数在 `tool_calls[i].function.arguments`（是 JSON 字符串，不是对象）{% endtab %}
{% endtabs %}

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
