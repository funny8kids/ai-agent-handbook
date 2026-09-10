---
tags: [prompt, engineering]
type: knowledge
status: published
updated: 2026-09-10
---

# 💬 结构化输出

> **一句话**：强制模型输出合法 JSON（或 XML/表格），是 Agent 把「概率文本」变成「可靠程序输入」的基石。
> **难度**：⭐️⭐️ 进阶
> **标签**：`#prompt` `#engineering`

## 📌 先看结论

- 四种实现强度：few-shot 示范 < JSON Mode < Schema 约束（Structural Outputs）< 约束解码（grammar 级，100% 合法）
- 结构化 ≠ 正确：格式合法不代表内容对，校验逻辑永远要自己写
- 工具调用的参数本质就是结构化输出——Agent 稳定性的一半在这里

## 🧩 实现方式对比

| 方式 | 原理 | 合法率 | 适用 |
|---|---|---|---|
| few-shot 示范 | 例子里给 JSON 样式 | 中 | 快速原型 |
| JSON Mode | 服务端保证输出合法 JSON | 高 | 无 schema 需求 |
| Structured Outputs | 按 JSON Schema 约束生成 | 很高 | 生产 API |
| 约束解码 | 逐 token 过滤非法候选 | 100% | 本地推理（outlines、xgrammar） |

## 💻 代码示例

```python
from pydantic import BaseModel
from openai import OpenAI

class Ticket(BaseModel):
    category: str      # billing / tech / other
    urgency: int       # 1-5
    summary: str

client = OpenAI()
resp = client.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": text}],
    response_format=Ticket,          # schema 级约束
)
ticket = resp.choices[0].message.parsed   # 直接得到对象
```

## 📦 源码案例

- **工具调用的本质**（[Function Calling](../05-tool-protocol/function-calling.md)）：模型输出的 `tool_use` 块就是结构化 JSON——名字、参数全部对齐你注册的 schema。Claude Code 逆向分析显示其 27 个内置工具全部带严格参数 schema，且用「延迟加载」控制 schema 占用的上下文预算
- **DeepSeek Harness 的工具 schema 组装**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：`core/system-prompt` 包每一步（preStep）动态组装工具 schema——工具面变化时模型看到的约束实时更新；其 PTC 模式更进一步：让模型直接写 Python 代码组合多次工具调用，把「结构化」升级为「程序化」
- **Pi 的 JSONL 会话**：会话事件本身用 JSONL 落盘，模型输出的工具调用与结果都是事件——结构化贯穿「模型输出 → 存储 → 回放」全链路

## ⚠️ 常见误区

- ❌ 格式合法就放心用：字段值可能超出枚举、数字越界——pydantic/JSON Schema 校验 + 拒绝重试才是完整闭环
- ❌ 一个大 schema 打天下：嵌套过深模型易漏字段，拆成多次调用更稳
- ❌ 忘记 max_tokens：输出被截断的 JSON 解析必炸，要捕获并重试

## 🧪 小练习

给「会议纪要提取」设计 schema（议题、决议、责任人、截止日期），并用 pydantic 写出校验逻辑，思考哪类非法值要触发重试。

## 📚 相关知识点

- [Prompt Engineering](prompt-engineering.md)
- [Function Calling](../05-tool-protocol/function-calling.md)
