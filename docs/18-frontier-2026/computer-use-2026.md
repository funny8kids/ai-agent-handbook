---
tags: [computer-use, browser-use, astra, claude]
type: knowledge
status: published
updated: 2026-09-22
---

# Computer Use 2026

{% hint style="info" %}
**一句话**：2026 的 computer use 已从「能点 GUI」变成 **产品级代办能力**——更快的视觉定位、任务边界遵守、企业白名单与自动审查成为标配。
{% endhint %}

## 先看结论

- 前沿分数：OSWorld 2.0 上 Astra 约 72.6%（partial），Fable 5.1 公布 partial 77.9% / strict 41.7%（配置不同，不可直接混比）
- 效率同样关键：Astra 官方称较 GPT-5.6 Sol 约 **47% 更少时间/任务**
- 安全成为产品功能：网站/应用白名单、确认策略、对高后果动作的自动审查
- 与 [05 章基础](../05-tool-protocol/computer-use-browser-use.md) 的差别：本页对齐 2026 产品与读数

![Computer use 回路与企业闸门](../.gitbook/assets/18-computer-use-loop.svg)

*《图：左半是经典感知—操作回路，右半是 2026 新加的企业闸门——白名单、上传下载策略、高后果确认；分数之外，闸门才是产品差异》*
## 核心机制

### 1. 感知—定位—操作回路

$$
a_t = \pi\big(s_t^{\text{screen}},\; g,\; h_{<t}\big),\qquad
s_{t+1} = \mathrm{Env}(a_t)
$$

$$s_t^{\text{screen}}$$ 可以是截图、可访问性树、DOM 或三者混合。混合感知通常比纯像素更稳。

### 2. 记分：partial vs strict

| 模式 | 含义 | 影响 |
|---|---|---|
| partial | 部分子目标达成给部分分 | 分数更高，贴近过程质量 |
| strict | 全部达成才算过 | 更接近「能否托付」 |

读榜单必须看清模式，否则会把 77.9% partial 和 41.7% strict 误比。

### 3. 企业闸门

2026 主流部署默认：

1. 允许站点/应用列表  
2. 上传下载策略  
3. 确认策略（付款、删除、外发）  
4. 工具调用自动审查  

见 [2026 安全现实](../10-evaluation-safety/safety-incidents-2026.md)。

### 4. 定位失效的恢复阶梯

GUI 自动化的头号故障不是「模型不会点」，而是**上一次截图里的元素这一次不在了**：页面异步渲染、列表重排、弹窗遮挡、滚动位置漂移都会让坐标失效。生产实现普遍按阶梯降级，而不是原地重试同一个坐标：

```python
# 伪代码：定位失效的四级降级阶梯（非完整实现）
def act_with_recovery(env, target, budget):
    for level in ("ax", "text_anchor", "zoom", "human"):
        ref = env.locate(target, method=level)   # 逐级换定位方式
        if ref is None:
            continue
        result = env.act(ref)                     # 点击 / 输入 / 选择
        if env.changed_as_expected(result):       # 用截图 diff + 状态断言判定
            return result
        budget.spend(level)                       # 每级都要计费，防止无限重试
    return env.escalate(target, reason="locate_exhausted")
```

三条要点：

1. **可访问性树（AX tree）优先于像素**：AX 节点带 role 与 name，页面重排后仍能按语义找到；纯坐标只在没有 AX 的原生应用里兜底。
2. **文本锚点比坐标稳**：「点『提交』右侧那个开关」这种描述，重排后命中率明显高于绝对坐标——写提示词时就把目标描述成语义锚点。
3. **判定成功要独立于模型自述**：模型说「已提交」不算，要用截图区域 diff、URL 变化、后端状态查询这类外部信号确认，否则会把幻觉当成完成。

### 5. 预算是三维的

只限轮次的护栏会在「第 3 步就烧光 token」时失效。2026 的实现通常同时卡三个维度，任一触顶即停：

$$
B=\min\big(N_{\text{steps}},\; T_{\text{visual-token}},\; W_{\text{wall-clock}}\big)
$$

再加一条**进展判据**：连续 $$k$$ 步（经验上取 2–3）页面状态没有可检测变化，就判定为原地打转而提前终止——这一步比单纯放宽轮次更省成本，因为它砍掉的正是「反复截图反复滚动」的无效循环。

## 常见误区

- ❌ **有 API 却硬用 GUI**：GUI 是「没有接口时的兜底」，不是更高级的能力。同一动作走 API 少两次截图往返，且不会因改版失效。
- ❌ **把 partial 分数当可托付度**：partial 77.9% 与 strict 41.7% 是同一系统的两种口径，选型要按你的容错场景挑口径，不能混比。
- ❌ **每步都截全屏**：视觉 token 随分辨率平方级增长；滚动后只截变化区域，或先取 AX 树再按需截图。
- ❌ **确认弹窗交给模型自己判断**：付款、删除、外发这三类动作的确认必须由 harness 侧的闸门触发，而不是模型「觉得需要问」。

## 小练习

给「在网页报销系统里提交一张差旅发票」设计 computer use 方案：写出感知方式（AX/DOM/截图各承担什么）、四级定位阶梯的具体判据、三维预算的取值，以及哪一步必须停下来问人。

## 工程含义

1. **优先 API/工具，其次 GUI**——有官方 API 的系统不要用 computer use 硬点
2. **每任务截图预算**：视觉 token 很贵；滚动与局部截图策略要设计
3. **失败模式入库**：误点、过期元素、验证码，都要有恢复路径

## 参考资料

- [GPT-6 Astra](https://openai.com/index/gpt-6-astra/)
- [Claude Fable 5.1 and Mythos 5.1](https://www.anthropic.com/claude-fable-and-mythos-5-1)
- [OSWorld](https://os-world.github.io/)
- [Anthropic Computer Use](https://docs.anthropic.com/en/docs/agents-and-tools/computer-use)

## 相关知识点

- [Computer Use / Browser Use](../05-tool-protocol/computer-use-browser-use.md)
- [通用 Agent 产品](../12-applications/general-agent-products.md)
- [评估 2026](eval-2026.md)

