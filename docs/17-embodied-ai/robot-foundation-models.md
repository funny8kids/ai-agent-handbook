---
tags: [embodied-ai, llm, advanced]
type: knowledge
status: published
updated: 2026-09-10
---

# 机器人基础模型谱系

> **一句话**：机器人基础模型（Robot Foundation Model）= 拿互联网规模的视觉语言先验，再用机器人轨迹把「看图说话」改造成「看图动手」——2023 年 RT-2 证明这条路能走，2024–2026 年的竞赛全在「动作头怎么做、数据从哪来、能不能上真机」。
> **难度**： 进阶
> **标签**：`#embodied-ai` `#llm`

## 先看结论

- **三个决定性设计选择**：① 动作表示（离散 token / 扩散 / flow matching）；② 是否分快慢双系统；③ 训练数据混合比（机器人轨迹 vs 网络视频 vs 仿真）。看任何新模型，先问这三条。
- **开源基线已经能用**：OpenVLA（7B，离散动作 token）、RDT-1B（扩散 Transformer）、SmolVLA（约 0.5B，消费级 GPU 可跑）是复现与二次开发最常拿来当起点的三个；π0 的 openpi 让「有 VLM + 有数据」的团队也能训出可用策略。
- **闭源前沿的共性是「双系统 + 高频动作专家」**：慢系统 VLM 出意图（约 5–10Hz），快系统小模型出动作（100–200Hz 甚至更高），中间靠 action chunk 与残差补偿。
- **不要拿 benchmark 分数横向比**：不同模型的任务集、演示数据量、评测协议（真机复位次数、是否允许重试）差异巨大；可比的是「同一评测协议下的相对提升」。

## 时间线速览

| 时间 | 代表工作 | 关键想法 |
|---|---|---|
| 2022–2023 | PaLM-E、RT-1、RT-2 | 把机器人数据与网络多模态数据一起训；动作写成 token 让 VLM「直接输出」 |
| 2023 | Open X-Embodiment / RT-X | 跨机构、多机型数据汇聚（百万轨迹量级），证明正迁移存在 |
| 2023 | ACT（Action Chunking with Transformers）、Diffusion Policy | 动作分块 + 扩散头，成为模仿学习的两项标配 |
| 2024 | OpenVLA、RDT-1B、Mobile ALOHA、UMI、DROID | 开源权重 + 高质量数据 + 免机器人采集，学界能上车了 |
| 2024–2025 | π0 / π0-FAST、GR00T N1、GO-1、Gemini Robotics、Helix | 商用/半开源基础模型：flow matching 动作专家、双系统、人形上半身 |
| 2025–2026 | π0.5、SmolVLA、GR00T N1.x 迭代、各家世界模型 | 家庭开放环境泛化、小模型端侧可用、合成数据（DreamGen 类）与视频预训练进入主战场 |

> ⚠ **注意**：上表是「思想脉络」而非版本清单；模型迭代极快，具体能力、参数、开源许可请以官方发布为准。

## 横向对比（架构视角）

| 模型 | 规模 | 动作头 | 控制方式 | 数据 | 开源 |
|---|---|---|---|---|---|
| RT-2 | 55B 级（PaLI-X/PaLM-E 底座） | 离散动作 token | 自回归逐步输出 | 网络 VLM 数据 + RT-1 机器人数据 | 否 |
| OpenVLA | 7B | 离散 token（256 bin/维） | 自回归，LoRA 微调友好 | OXE（约百万轨迹） | 是（权重 + 训练） |
| RDT-1B | 1.2B | 扩散 Transformer | 一次预测一段动作块 | 跨具身数据（双臂桌面为主） | 是 |
| π0 | 约 3B VLM + 约 0.3B 动作专家 | flow matching | 50Hz 动作块，高频连续 | 自有 + 开放多机型数据 | 权重/训练码部分开源（openpi） |
| GR00T N1 系 | VLM（Eagle 系）+ DiT | 扩散/流式动作专家 | 双系统，DiT 高频出动作 | 真机 + 合成视频 + 人类视频混合 | 是（权重开源，配套 Isaac/Sim） |
| Helix | S2 约 7B VLM / S1 约 0.1B | 快速视觉运动 Transformer | 约 7–9Hz + 200Hz 分层 | 数百小时高质量双臂/人形遥操 | 否 |
| GO-1 | 大规模 VLA | ViLLA（含 latent action） | 分层：latent 动作衔接 | AgiBot World 大规模遥操 | 部分开源 |
| Gemini Robotics | 基于 Gemini 2.0 | 动作 token / API 化控制，另有 ER 推理模型 | 高延迟靠动作块补偿 | 多机型（ALOHA 2、双臂） | 否（API/受限） |
| SmolVLA | 约 0.45B | 流式动作专家 | 消费级 GPU 上可跑，多数据集联合训练 | AgiBot World / DROID / OXE 等 | 是 |

**读表三问**：动作头是离散还是连续（决定高频控制可行性）？有没有快慢分层（决定实时性与算力预算）？训练数据里真机轨迹占比多少（决定泛化是否可迁移到你的机器人）？

## 选型建议（按你要做的事）

| 你的情况 | 建议起点 | 理由 |
|---|---|---|
| 学校实验室 / 单人研究，1 条臂 + 夹爪 | OpenVLA 或 SmolVLA + LeRobot | 训练与推理门槛低，LoRA 微调流程成熟 |
| 有遥操作数据（几十小时以上），要做双臂桌面 | π0 系（openpi）或 RDT-1B | 连续动作头 + 动作块，接触类任务表现稳 |
| 要上人形/移动底盘、算力受限 | 双系统自研：小 policy + 云端 VLM | 板载算力是硬约束，见 [硬件、实时与安全](hardware-realtime-safety.md) |
| 需要完全可审计、可微调、私有部署 | 开源权重（OpenVLA/GR00T/SmolVLA） | 闭源 API 无法改动作头，也难以离线迭代 |
| 只是想验证「能不能做这个任务」 | 先在仿真里跑开源 checkpoint + 你自己的评估集 | 见 [仿真与 Sim-to-Real](simulation-sim2real.md)、[评估与基准](evaluation-benchmarks.md) |

## 工程现场笔记

- **动作 token 化的坑**：早期方案把每维动作量化成 256 个 bin 当 token 输出，优点是复用 LLM 训练栈、缺点是高频控制时 token 数暴涨（50Hz × 50 步 × 7 维 = 17500 token/秒）。这就是 flow matching / 扩散头成为新共识的原因，见 [VLA 模型架构](vla-models.md)。
- **「零样本」是相对的**：模型宣称的零样本泛化，通常在新环境 + 新物体上成立，但在新的**观测布局**（相机视角变了）、新的**动作空间**（夹爪换成灵巧手）上会失效。迁移成本要按「重采数据 + 微调」来估。
- **底座换 VLM 不一定更好**：更大 VLM 带来的语义提升，常常被推理延迟与板载显存抵消。行业实践是「慢系统可以大、快系统一定要小」。
- **开源许可要看清**：模型权重、训练代码、数据许可常是三套条款（非商用限制、数据仅限研究）。进产品前逐条确认。

## 常见误区

- ❌ 拿 demo 视频当能力证明：demo 是挑选后的样本，成功率与任务数必须来自评测协议
- ❌ 用「参数量」比模型好坏：机器人模型的关键在动作头与数据，不在 VLM 底座大小
- ❌ 以为微调一下就会你的任务：动作空间、相机、控制频率、物体尺度任一变化都需要相应数据
- ❌ 忽视动作延迟模型：训练时假设「观测→动作 0 延迟」，真机有 20–100ms 延迟，不做延迟建模就会抖（→ [动作表示与分层控制](action-representation-control.md)）
- ❌ 把跨具身数据当成免费午餐：正迁移存在，但形态差异大时负迁移也常见，需要按机型/动作空间做配比与掩码

## 小练习

挑表中两个模型（建议 π0 与 OpenVLA），分别写出：动作头形式、一次推理输出多少步、单步控制频率、需要多少演示数据才可能微调成功。然后回答：如果你的相机只有 30fps 且板载 16GB 显存，哪个更现实？

## 相关资源

- [RT-2 论文](https://arxiv.org/abs/2307.15818)、[Open X-Embodiment](https://arxiv.org/abs/2310.08864)、[OpenVLA](https://github.com/openvla/openvla)、[π0](https://arxiv.org/abs/2410.24164)、[openpi](https://github.com/Physical-Intelligence/openpi)
- [RDT-1B](https://arxiv.org/abs/2410.07864)、[GR00T N1](https://arxiv.org/abs/2503.14734)、[SmolVLA](https://huggingface.co/blog/smolvla)、[GO-1](https://arxiv.org/abs/2503.06669)

## 相关知识点

- [VLA 模型架构](vla-models.md)
- [数据引擎](data-engine.md)
- [多模态模型](../03-llm/multimodal.md)
- [推理经济学与部署形态](../16-ai-infrastructure/inference-economics-deployment.md)
