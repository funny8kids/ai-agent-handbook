---
tags: [tooling, paper]
type: resource
status: published
updated: 2026-09-22
---

# Toolformer 论文

{% hint style="info" %}
**一句话**：证明语言模型可以通过自生成的数据学会「何时、如何调用工具」——工具使用从「外挂工程」变成「模型能力」的起点。
{% endhint %}

| 属性 | 内容 |
|---|---|
| 类型 | 论文 |
| 链接 | <https://arxiv.org/abs/2302.04761> |
| 来源 | Schick et al., Meta AI |
| 发布 | 2023-02 |
| 难度 | 进阶 |
| 标签 | `#tooling` `#llm` |

## 推荐理由

- 自监督数据构造思路精妙：模型自己标注「在哪里插入 API 调用有帮助」
- 677M 的 GPT-J 学会工具调用后胜过数倍大的 GPT-3——工具弥补能力缺口的早期实证
- 理解今天 Function Calling 训练范式的思想源头

## 机制一图看懂

采样 → 过滤 → 微调三步，数据完全由模型自己标注：

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#EDEEF0","primaryBorderColor":"#475569","primaryTextColor":"#1F2937","secondaryColor":"#D7DADE","tertiaryColor":"#F8F8F9","lineColor":"#9AA2AD","actorBkg":"#F0F1F3","actorBorder":"#475569","actorTextColor":"#1F2937","signalColor":"#7E8896","noteBkgColor":"#DEE0E4","noteBorderColor":"#475569","noteTextColor":"#1F2937","labelBoxBkgColor":"#EDEEF0","labelBoxBorderColor":"#475569"}}}%%
flowchart TD
    D["无标注文本"] --> M["模型自采样：在哪些位置插入 API 调用可能有帮助？"]
    M --> S["候选数据：含工具调用 token 的变体"]
    S --> P{"对比困惑度：插入调用后预测变好了吗？"}
    P -->|"变差"| X["丢弃该调用"]
    P -->|"变好"| K["保留：自标注训练数据"]
    K --> FT["微调基座模型"]
    FT --> R["模型学会何时、如何调用工具"]
```

## 上手建议

1. 读第 3 节方法（采样 → 过滤 → 微调三步）
2. 关注它选的五个工具（计算器/问答/搜索/翻译/日历）与各自的触发场景
3. 对照现代 [Function Calling](../../05-tool-protocol/function-calling.md)：今天的 API 已把这套训练成果产品化

## 参考资料

- [Toolformer 论文](https://arxiv.org/abs/2302.04761)（Schick et al., 2023，Meta AI）
- 官方未释出训练代码与权重，复现以论文正文与附录的实验设置为准

## 相关知识点

- [Function Calling](../../05-tool-protocol/function-calling.md)
- [Tool Use](../../05-tool-protocol/tool-use.md)

