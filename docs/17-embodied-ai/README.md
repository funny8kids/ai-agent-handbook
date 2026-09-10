---
tags: [embodied-ai, agent, index]
type: index
status: published
updated: 2026-09-10
---

# 17 具身智能

> **一句话**：具身智能（Embodied AI）是把「会想的大脑」接进「会动的身体」——难点不在让模型说出步骤，而在把 5Hz 的语义决策变成 50–1000Hz 的电机指令，同时还能承受真实世界的噪声、磨损与安全事故。

## 先看结论

- **LLM Agent 与机器人 Agent 是同一套循环的两种实现**：感知 → 规划 → 行动 → 观测反馈。差别在于机器人的「工具调用」不可回滚（杯子已经掉了），奖励信号延迟且昂贵，一次失败要人工复位。
- **控制频率决定架构**：VLM 级推理只有 5–10Hz，电机控制需要 50Hz–1kHz。所以现代方案基本都是**双系统 / 快慢分层**：慢系统给意图，快系统出动作，靠 action chunking 或残差策略把频率断层补上。
- **数据是最大瓶颈，不是模型结构**：机器人轨迹比文本贵 4–6 个数量级。整个领域在争的其实是四条数据路线的成本曲线：遥操作、手持/无机器人采集、仿真合成、人类视频。
- **仿真解决「量」，真机解决「对不对」**：sim-to-real 的差距来自接触、摩擦、延迟、相机曝光与标定；域随机化能把策略「训 robust」，但无法保证真机指标可外推。
- **安全是硬件属性，不是软件承诺**：力矩限制、功率与力限制（PFL）、急停回路、速度与安全层（SSL）、工作空间围栏——任何「模型更小心了」都不构成安全论证。

## 本章地图

| 页面 | 回答什么问题 |
|---|---|
| [什么是具身智能](what-is-embodied-ai.md) | 定义、与 LLM Agent 的异同、莫拉维克悖论、三代技术范式 |
| [机器人基础模型谱系](robot-foundation-models.md) | RT-2 → OpenVLA → π0 → GR00T / Helix / GO-1 / Gemini Robotics：能力与代价对比 |
| [VLA 模型架构](vla-models.md) | 视觉编码、语言条件、动作头（离散 token vs 扩散 vs flow matching） |
| [动作表示与分层控制](action-representation-control.md) | 动作空间怎么设计、控制频率怎么对齐、慢脑快脑如何协同 |
| [数据引擎](data-engine.md) | 遥操作、UMI、众包、视频、仿真合成、飞轮与配比 |
| [仿真与 Sim-to-Real](simulation-sim2real.md) | Isaac Lab / MuJoCo / Genesis、域随机化、real2sim、接触仿真陷阱 |
| [世界模型与视频预训练](world-models-video.md) | 用视频学物理常识：Genie / V-JEPA / Cosmos 类，能替代真机数据吗 |
| [灵巧操作](manipulation.md) | 抓取、可操作物品推理、触觉、灵巧手、接触丰富任务 |
| [人形与腿足运动](humanoid-locomotion.md) | RL 运动控制、全身控制、遥操数据学步态、人形到底解决什么 |
| [评估与基准](evaluation-benchmarks.md) | LIBERO / CALVIN / SimplerEnv / BEHAVIOR、真机评测协议、成功率怎么报 |
| [硬件、实时与安全](hardware-realtime-safety.md) | 传感器、边缘算力、ROS 2 / EtherCAT、急停与力限制 |
| [把 Agent 接进机器人](agent-to-robot-bridge.md) | 任务规划层 + 技能库 + ROS 2 桥接，含可跑的最小代码 |

## 动态图示

| 图示 | 说明 |
|---|---|
| [VLA 感知—决策—行动回路](../assets/diagrams/17-vla-loop.svg) | 帧进入、慢系统出意图、快系统出动作块，两条时钟怎么对齐 |
| [Action Chunking 与异步执行](../assets/diagrams/17-action-chunking.svg) | 5Hz 推理为什么能驱动 50Hz 控制：滚动地「预取」未来动作 |
| [域随机化与 Sim-to-Real](../assets/diagrams/17-sim2real-domain-randomization.svg) | 随机化「训练时的分布」而不是「调一个最像真的场景」 |

## 阅读建议

- **软件工程师转过来**：[什么是具身智能](what-is-embodied-ai.md) → [VLA 模型架构](vla-models.md) → [把 Agent 接进机器人](agent-to-robot-bridge.md)，然后照 [仿真与 Sim-to-Real](simulation-sim2real.md) 装个仿真器跑通一次
- **算法方向**：[数据引擎](data-engine.md) 与 [世界模型](world-models-video.md) 是当前最活跃的战线
- **做产品/做集成**：[硬件、实时与安全](hardware-realtime-safety.md) → [评估与基准](evaluation-benchmarks.md)（先定义怎么验收，再谈模型能力）
- 与 [16 AI 基础设施](../16-ai-infrastructure/README.md) 的连接：机器人是「延迟预算最苛刻的推理客户端」——同一套量化/分层/降级思路，只是单位从「毫秒体验」变成「毫秒不掉杯子」

## 相关知识点

- [多模态模型](../03-llm/multimodal.md)
- [Agent 核心组件](../02-agent-basics/core-components.md)
- [Computer Use / Browser Use](../05-tool-protocol/computer-use-browser-use.md)
- [游戏 Agent](../12-applications/game-agent.md)
