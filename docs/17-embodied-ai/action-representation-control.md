---
tags: [embodied-ai, engineering]
type: knowledge
status: published
updated: 2026-09-23
---

# 动作表示与分层控制

{% hint style="info" %}
**一句话**：模型输出的从来不是「动作」，而是某个坐标系下、某个频率上、经过限幅的一段目标——动作表示选错，再强的策略网络也只会稳定地失败。
  **难度**： 进阶
{% endhint %}

## 先看结论

- **表示优先于网络**：90% 的「模型不work」在这一步就能避免：末端位姿增量（相对当前）比绝对位姿好学；关节位置目标比力矩目标好部署；绝对旋转用四元数或 6D 表示，不要用欧拉角（万向锁 + 不连续）。
- **控制频率分层**：VLM/规划 1–10Hz → 动作策略 30–200Hz → 关节伺服/平衡控制 500Hz–1kHz+ → 电流环数 kHz。层间用「意图 + 残差」或「目标 + 插值」连接，不要用一层去顶所有层。
- **必须显式建模延迟**：推理 50–200ms、通信 1–20ms、执行器响应一阶滞后。训练时注入随机延迟，部署时做观测时间戳对齐与动作外推，否则策略会「越修正越振荡」。
- **安全层在模型外面**：位置/速度/力矩限幅、关节软限位、自碰撞检查、末端力上限、急停（硬件回路）——模型输出先过这道闸门，永远不要相信神经网络会自律。

## 动作空间怎么选

| 表示 | 优点 | 代价 | 适用 |
|---|---|---|---|
| 末端位姿增量 Δ(x,y,z,rot) + 夹爪 | 与相机视觉最相关、跨机型迁移好 | 需要 IK/笛卡尔控制器；误差累积 | 桌面操作、VLA 微调（最常用） |
| 绝对末端位姿 | 无累积误差 | 分布偏移大，物体一动就废 | 固定工装、结构化抓取 |
| 关节位置目标 | 部署最简单、天然平滑 | 与视觉关系弱，泛化差 | 单臂固定任务、数据来自同一机型 |
| 关节速度 | 安全好限幅 | 精度差，慢 | 教学/演示、早期原型 |
| 力矩 / 关节阻抗 | 能做接触丰富任务（插拔、擦、推） | 需要动力学模型或大量数据；调参敏感 | 装配、人形全身控制 |
| 基座速度（v, ω） | 移动操作解耦简单 | 需要定位与地图 | 轮式底盘、移动机械臂 |

> 💡 **提示**：混合动作空间很常见——「末端增量 + 夹爪开合 + 底盘速度」三段拼接，各自限幅方式不同。写清楚每段的单位、符号约定与坐标系（base / wrist / camera），写进数据 schema，别只写在 README。

## 分层控制与频率对齐

![慢脑—快脑—伺服的时钟关系](../.gitbook/assets/17-action-chunking.svg)

*《图：5Hz 推理喂 50Hz 控制的办法是发动作块——重叠段做时间集成所以边界不跳变，力超限或物体被碰走则丢弃剩余动作立刻重推》*
```text
任务层   1–10Hz   「先去水槽那边，再抓蓝色杯子」        ← LLM/VLM、行为树、状态机
技能层  30–200Hz  动作块 a₁…a₅₀（Δ位姿 + 夹爪）        ← VLA / diffusion / flow 策略
控制层 0.5–1kHz   笛卡尔速度→IK→关节目标→阻抗/PD        ← 控制器、QP、WBC
驱动层   kHz+     电流环、力矩补偿、摩擦与前馈            ← 厂商固件/实时总线（EtherCAT 等）
```

**为什么必须分频**：慢系统的算力（几十 GB 权重）跑不到 50Hz，快系统的显存与算力又不足以理解语义。所以慢系统只交「意图」，快系统持续修正，底层负责稳定与限幅——这也是 [VLA 双系统架构](vla-models.md) 存在的物理原因。

## Action Chunking 与「滚动重规划」

部署侧的核心不是「模型跑一次」，而是「边执行当前块、边并行算下一块」。下面这份 JSON 描述滚动缓冲的状态：`H` 是块长、`overlap` 是和新块加权重叠的步数、`prefetch_ahead` 是提前多少步发起下一次推理。三个数决定这条流水线断不断流。

```json
{
  "chunk_buffer": {
    "H": 50,
    "control_hz": 50,
    "duration_s": 1.0,
    "overlap": 15,
    "prefetch_ahead": 8
  },
  "per_tick_loop": [
    "capture obs",
    "pop plan[i]",
    "clamp(a, joint_limits, vel_limit, torque_limit)",
    "if force_exceeded: hold_and_replan",
    "send(a)",
    "if i >= len(plan)-8: submit next inference",
    "sleep_at(control_hz)"
  ],
  "blend": { "method": "temporal ensembling", "scope": "overlap=15 步加权平均", "why": "消除块边界跳变" },
  "replan_trigger": ["force_exceeded", "large_visual_displacement", "stall_detected"]
}
```

一次控制周期就是 `per_tick_loop` 那七步：取 `plan[i]`、`clamp`（同时夹 `joint_limits`/`vel_limit`/`torque_limit`）、发命令；当 `i >= len(plan) - prefetch_ahead`（示例剩 8 步）就把后台算好的 `new_plan` 接上——`H=50`、`control_hz=50`、重叠 `overlap=15` 是同一份配置里的数。

### 一次滚动重规划（分步演示）

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#F8EEE6","primaryBorderColor":"#B45309","primaryTextColor":"#1F2937","secondaryColor":"#EFD9C9","tertiaryColor":"#FCF8F5","lineColor":"#D6A078","actorBkg":"#F9F1EB","actorBorder":"#B45309","actorTextColor":"#1F2937","signalColor":"#CB8753","noteBkgColor":"#F2E0D3","noteBorderColor":"#B45309","noteTextColor":"#1F2937","labelBoxBkgColor":"#F8EEE6","labelBoxBorderColor":"#B45309"}}}%%
sequenceDiagram
    participant R as 实时线程
    participant B as 缓冲 plan
    participant P as 后台推理
    R->>B: 取 plan[i]
    B-->>R: 动作 a
    R->>P: 剩 8 步时提交新观测
    P-->>B: new_plan（旧观测算出）
    Note over B: blend：重叠 15 步加权
```

*《图：实时线程只管从缓冲取动作，推理在后台并行；交接点靠 15 步重叠加权，避免边界跳变》*

{% stepper %}
{% step %}

#### 第 1 步：出块

`policy.step(obs, instruction)` 返回长度 `H=50` 的动作列表（每维是本页 schema 里的 `Δxyz + 6D + 夹爪`）。慢系统 5Hz、控制 50Hz，一次必须出 1 秒的量。

{% endstep %}
{% step %}

#### 第 2 步：逐拍取动作 + 限幅

每个控制拍 `pop plan[i]`，先 `clamp(a, joint_limits, vel_limit, torque_limit)`——安全层在模型外面，永远不信网络会自律。然后 `robot.send(a)`，`sleep_at(CONTROL_HZ)` 卡在 50Hz。

{% endstep %}
{% step %}

#### 第 3 步：提前发起下一次推理

剩 `prefetch_ahead=8` 步（`i >= len(plan) - 8`）时，后台线程用新观测提交 `new_plan`。为什么提前？推理要 50–200ms，等块跑完才算，中间就有「闭眼执行」的断流窗口。

{% endstep %}
{% step %}

#### 第 4 步：重叠段做时间集成

新块就绪，`blend(plan[i:], new_plan[:len-i], overlap=15)`——重叠的 15 步加权平均（ACT 论文的 temporal ensembling），块边界不跳变。`i` 归零，继续吐。

{% endstep %}
{% step %}

#### 第 5 步：异常触发式重算

`force_exceeded` / 视觉大位移 / 卡滞命中 → 立即 `hold_and_replan`：丢弃剩余块、保持当前位姿、用最新观测重推。别硬着头皮把 1 秒动作执行完——这是 [灵巧操作](manipulation.md) 里接触异常闸门的同一套逻辑。

{% endstep %}
{% endstepper %}

### 每种表示怎么坏（点标签切换）

同一张动作空间表（见上）给的是优点，这里补上各自的**失效场景**——选错表示往往不是选到最差的，而是选到当前任务扛不住的那种。

{% tabs %}
{% tab title="末端位姿增量" %}
`Δ(x,y,z,rot)` 相对当前 TCP，和相机最相关、跨机型迁移最好，是 VLA 微调默认。坏在**误差累积**：每步一小偏，100 步后漂移可见；且强依赖 IK/笛卡尔控制器，接近奇异点时解算会突然爆。

{% endtab %}
{% tab title="绝对末端位姿" %}
无累积误差，适合固定工装、结构化抓取。坏在**分布偏移**：物体一动（被人碰、传送带挪），绝对目标就作废，策略没见过就完全不知道该往哪走。

{% endtab %}
{% tab title="关节位置目标" %}
部署最简单、轨迹天然平滑。坏在**泛化差**：与视觉关系弱，换机型、换初始姿态全得压给网络记，演示数据来自哪台机器就只在这台上好用。

{% endtab %}
{% tab title="力矩 / 阻抗" %}
能做插拔、擦、推这类接触丰富任务。坏在**要动力学模型或海量数据**、调参敏感，一个阻尼没配好整机就抖；所以产业上多半给策略一个阻抗接口，而不是让它裸出力矩。

{% endtab %}
{% tab title="离散动作原语" %}
把动作收成 `pick/place/wipe` 等有限 token，语言层直接挑。坏在**粒度太粗时高频控制做不了**（插不准、力控不了），太细则 token 数爆炸又回到「量化误差 + 解码慢」——这是 [VLA 离散 token 头](vla-models.md) 的老债。

{% endtab %}
{% endtabs %}

**要点**

- **blend（时间集成）**：重叠段做加权平均（ACT 论文里的 temporal ensembling 思路），消除块边界处的跳变。
- **触发式重算**：视觉出现大位移、力超限、卡滞 → 立刻丢弃剩余块重新推理，别硬着头皮把 1 秒动作执行完。
- **块长与任务匹配**：搬运（准静态）可 1–2 秒；插拔/擦桌子（接触反馈主导）应 0.2–0.4 秒；需要动态平衡的人形，快系统更短、底层反射独立。

## 单位与限幅的「一页规范」

```yaml
# action_spec.yaml —— 与数据管线、控制器、评估脚本共用同一份定义
frame: base_link           # 所有 xyz 在底座坐标系
rotation: 6d               # 6D 表示（Zhou et al.），不用欧拉角
order: [dx, dy, dz, r0, r1, r2, r3, r4, r5, gripper]
scale:
  translate: 0.05          # 每步最大 5 cm
  rotate: 0.15             # 每步最大约 8.6°
  gripper: 1.0             # 0=闭, 1=开
control_hz: 50
clamp:
  gripper_force_n: 40      # 超力即退回，防夹碎
  joint_pos: soft_limit    # 由 URDF 读入，留 5° 余量
latency:
  inference_ms: [40, 180]  # 训练时按此范围随机注入
timestamp: monotonic_ns; obs 与 action 必须带 ts 并做最近邻对齐
```

## 工程现场笔记

- **力/力矩反馈被低估**：只用视觉的策略在「插 USB、开抽屉、擦玻璃」这类任务上会一直失败——接触信号是必需的输入，不只是安全监控。
- **阻抗 vs 位置控制**：位置控制在接触时刚度极高（撞了就顶），阻抗/导纳控制允许「软」。学习型策略配阻抗接口，鲁棒性通常好一档。
- **人形的腰部/平衡不能被上层「微操」**：平衡是 kHz 级反射问题。产业方案是给策略一个「质心/落脚点/躯干姿态」接口，底层 WBC 负责不打晃（Helix 一类公开资料里「再加一层更快系统」的思路也是同一件事）。
- **状态估计要归一化一致**：训练与部署的关节单位、坐标系、偏置必须一致。业内常见事故：仿真用弧度、真机驱动回传角度，策略「看着合理」地乱挥。写自动校验（量级检查 + 单步最大变化检查）。

## 常见误区

- ❌ 让模型直接输出关节角度绝对值并期望泛化：不同机型/初始化差异全被压给网络记
- ❌ 欧拉角做旋转：±180° 跳变与万向锁让 MSE 学到荒谬的东西
- ❌ 控制频率与数据频率不一致还直接拼接：录 30Hz、控 50Hz，时间轴错位会让策略「学反因果」
- ❌ 把限幅写进 prompt / 语言层：语言层的「请轻一点」不是安全机制
- ❌ 不做动作平滑（rate limiter / jerk 限制）：电机与减速器寿命、整机抖动都会出问题，评审时也过不了

## 小练习

在仿真里做「延迟消融」：训练时假设 0 延迟，部署时分别注入 0 / 60 / 150 / 300ms 的观测—动作延迟，记录成功率与末端抖动幅度（加速度方差）。然后把随机延迟注入训练，重训一次看恢复多少。这个实验 1 小时能做完，却能让你彻底理解「延迟建模」为什么是标配。

## 参考资料

- [ACT/ALOHA 论文](https://arxiv.org/abs/2304.13705)（动作分块 + temporal ensembling 的出处）、[Diffusion Policy](https://arxiv.org/abs/2303.04137)
- [ROS 2 控制栈文档](https://control.ros.org/)、[Ompl / MoveIt 2](https://moveit.picknik.ai/)（经典规划与安全层参考实现）

## 相关知识点

- [VLA 模型架构](vla-models.md)
- [硬件、实时与安全](hardware-realtime-safety.md)
- [仿真与 Sim-to-Real](simulation-sim2real.md)
- [把 Agent 接进机器人](agent-to-robot-bridge.md)

