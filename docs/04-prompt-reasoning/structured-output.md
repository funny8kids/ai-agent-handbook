---
tags: [prompt, engineering]
type: knowledge
status: published
updated: 2026-09-10
---

# 结构化输出

> **一句话**：强制模型输出合法 JSON（或 XML/表格），是 Agent 把「概率文本」变成「可靠程序输入」的基石。

## 问题动机

模型是按概率逐 token 采样的，你写了「请输出 JSON」，它仍可能加上一段解释、用中文引号、或漏掉逗号——而对下游程序来说，一段无法解析的字符串等于彻底失败。Agent 的工具调用、参数抽取、报告生成全都依赖结构化输出，所以「怎么把合法率从 90% 提到 100%」是个硬工程问题。

## 核心机制

### 1. 约束解码：为什么能做到 100% 合法

普通采样从整个词表 $V$ 里按概率取 token：

$$
x_t\sim p(x_t\mid x_{<t})
$$

约束解码（constrained decoding）在每个解码步，只保留那些「加入后仍能通过语法/JSON Schema 前缀校验」的 token，其余概率置零后重新归一化：

$$
p'(x_t\mid x_{<t})=
\frac{p(x_t\mid x_{<t})\cdot\mathbb{1}\big[\,x_{<t}\oplus x_t\ \text{是合法前缀}\,\big]}
{\sum_{v\in V}p(v\mid x_{<t})\cdot\mathbb{1}\big[\,x_{<t}\oplus v\ \text{是合法前缀}\,\big]}
$$

$\mathbb{1}[\cdot]$ 是指示函数：当前缀违反了 schema（如该出 `,` 却出了字母），该 token 直接被排除。这样生成的序列**在语法层面必然合法**——这就是 outlines / xgrammar 一类工具能做到「100% 合法 JSON」的原理。

代价是：每步要算一次「哪些 token 允许」，实现上通常把 schema 编译成有限状态机或下推自动机，再对词表建索引加速。

### 2. 合法 ≠ 正确

约束解码保证的是**语法合法**，不保证**语义正确**。字段值可能超出枚举、数字越界、日期格式对但日期不存在。因此完整闭环是：

$$
\underbrace{\text{约束解码}}_{\text{保证语法}}
\;\longrightarrow\;
\underbrace{\text{Schema/业务校验}}_{\text{保证类型与范围}}
\;\longrightarrow\;
\underbrace{\text{拒绝重试}}_{\text{失败时回填错误}}
$$

缺了后两步，「100% 合法」只是把解析错误推迟到了业务层。

### 3. 四种实现方式的强度阶梯

$$
\text{few-shot} \;<\; \text{JSON Mode} \;<\; \text{Structured Outputs} \;<\; \text{约束解码}
$$

越往右，模型自由度越小、合法率越高，但需要的能力（服务端或本地运行时）也越强。

## 实现方式对比

| 方式 | 原理 | 合法率 | 适用 |
|---|---|---|---|
| few-shot 示范 | 例子里给 JSON 样式 | 中 | 快速原型 |
| JSON Mode | 服务端保证输出合法 JSON | 高 | 无 schema 需求 |
| Structured Outputs | 按 JSON Schema 约束生成 | 很高 | 生产 API |
| 约束解码 | 逐 token 过滤非法候选 | 100%（语法） | 本地推理（outlines、xgrammar） |

## 代码示例

```python
from pydantic import BaseModel, Field
from typing import Literal
from openai import OpenAI

class Ticket(BaseModel):
    category: Literal["billing", "tech", "other"]
    urgency: int = Field(ge=1, le=5)
    summary: str

client = OpenAI()
resp = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": text}],
    response_format=Ticket,          # schema 级约束
)
ticket = resp.choices[0].message.parsed   # 直接得到校验过的对象
```

## 源码案例

- **工具调用的本质**（→ [Function Calling](../05-tool-protocol/function-calling.md)）：模型输出的 `tool_use` 块就是结构化 JSON——名字、参数全部对齐你注册的 schema。Claude Code 的逆向分析显示其内置工具都带严格参数 schema，并用「延迟加载」控制 schema 占用的上下文预算
- **DeepSeek Harness 的工具 schema 组装**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：`core/system-prompt` 在每步 preStep 动态组装工具 schema——工具面变化时模型看到的约束实时更新；其 PTC 模式让模型直接写代码组合多次工具调用，把「结构化」升级为「程序化」
- **outlines**（[GitHub](https://github.com/dottxt-ai/outlines) / [论文](https://arxiv.org/abs/2307.09702)）：把 JSON Schema / 正则编译成状态机做约束解码的开源实现，是理解该机制最直接的参考

## 常见误区

- ❌ 格式合法就放心用：字段值可能超出枚举、数字越界——Schema 校验 + 拒绝重试才是完整闭环
- ❌ 一个大 schema 打天下：嵌套过深模型易漏字段，拆成多次调用更稳
- ❌ 忘记 `max_tokens`：输出被截断的 JSON 解析必炸，要捕获并重试
- ❌ 认为约束解码没有代价：它会让模型无法输出「我需要更多信息」这类自然语言，必要时保留逃生出口

## 参考资料

- [Efficient Guided Generation for Large Language Models](https://arxiv.org/abs/2307.09702)（Willard & Louf, 2023，outlines）
- [Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning](https://arxiv.org/abs/2305.13971)（Geng et al., 2023）
- [JSON Schema 规范](https://json-schema.org/)

## 相关知识点

- [Prompt Engineering](prompt-engineering.md)
- [Function Calling](../05-tool-protocol/function-calling.md)
