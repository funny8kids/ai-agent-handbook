---
tags: [embodied-ai, evaluation]
type: knowledge
status: published
updated: 2026-09-10
---

# 🦾 评估与基准：怎么证明机器人真的行

> **一句话**：机器人评估的第一原则是「一次成功是一次成功」——不允许无限重试、不允许剪辑、不允许只报最好那次；比分数更重要的是评测协议（任务集、初值分布、成功判据、失败分类）能否被别人复现。
> **难度**：⭐️⭐️ 进阶
> **标签**：`#embodied-ai` `#evaluation`

## 📌 先看结论

- **成功率必须带置信区间和试验次数**：`18/20 = 90%` 与 `450/500 = 90%` 不是一回事；报数字必须同时报 n、任务/物体分布、复位方式。
- **区分三种「成功率」**：`per-attempt`（每次尝试）、`per-episode-with-retries`（允许重试，虚高）、`user-facing`（含人工复位、卡死求助的真实完成率）。产品要盯最后一条。
- **泛化要用「留出集」而不是「新描述」**：留出物体类别、留出场景、留出光照、留出相机视角——四个维度分别测，才知道模型到底学到了什么。
- **基准分数跨基准不可比**：LIBERO、CALVIN、SimplerEnv、BEHAVIOR 的任务、指标、评测协议完全不同。可比的是「同一协议下你与基线之差」。
- **安全指标与能力指标要一起报**：最大接触力、越界次数、急停触发率、异常噪声——否则「更激进 = 分数更高」会诱导策略鲁莽。

## 🗺️ 常见基准

| 基准 | 类型 | 关注点 | 什么时候用 |
|---|---|---|---|
| CALVIN | 仿真（语言条件长时序） | ABC→D 划分、多步串联（min/max 步数） | 语言→动作的长时序能力快速迭代 |
| LIBERO | 仿真（ lifelong/结构变体） | 空间、物体、目标、知识四组任务 | 微调后是否忘旧学新、快速回归 |
| SimplerEnv | 仿真复现真机 | 用真机初始状态在仿真里 rollout，估计真机成功率 | 想低成本、大批量估真机指标 |
| RLBench / ManiSkill3 | 仿真任务套件 | 任务面广、GPU 并行、可脚本化判据 | 大规模 RL / 数据生成 / 快速验证 |
| BEHAVIOR-1K / RoboCasa | 仿真（家务长时序） | 1000 项活动、需状态与物体交互 | 家庭场景、长时序规划 |
| Open X-Embodiment / DROID / AgiBot World | 数据集（含评测子集） | 跨机型、多场景真机轨迹 | 训练与「跨具身」泛化研究 |
| 自建真机协议 | 真机 | 你的产品任务 | 上线验收的唯一依据 |

> ⚠️ **注意**：仿真基准分数很容易被「针对基准过拟合」——把基准里的相机、桌面、物体形状当成部署目标。上线前必须有一组你自己的、从基准格式独立出来的真机任务。

## ⚙️ 一份可复制的真机评测协议

```yaml
# eval_protocol.yaml —— 交给操作员和统计脚本各一份，别口述
tasks:
  - id: cup-to-sink
    instruction_pool:            # 同一任务多种说法，防「记住了话术」
      - "把桌上的杯子放进水槽"
      - "收一下杯子，放水槽里"
    initial_state:
      object_pose: uniform(x: [0.1,0.5], y: [-0.3,0.3], yaw: [-180,180])
      distractors: [tissue, sponge]        # 干扰物随机摆放
      lighting: [day, night-lamp, backlit]
      camera_extrinsics: nominal ± 2deg
    success:                      # 必须自动可判（或明确的人工判据）
      - cup.center inside sink.polygon
      - gripper.openness > 0.9 AND no_contact_for: 2s
    partial_credit:               # 过程分，比 0/1 更有信息量
      cup_moved_pct: distance_traveled / distance_required
      wrong_place_penalty: -0.3
    retry: none                   # 关键：一次机会；另设 reset-assisted 统计
    trials: 20                    # 每组条件 ≥20，最好 50
trials_report:
  n: 100          # 总尝试数
  success: 61
  rate: 0.61      # Wilson 95% CI: [0.51, 0.70]
  failures: {slip: 14, wrong_target: 9, stuck: 8, timeout: 5, safety_stop: 3}
  median_seconds: 41
  human_resets_per_task: 0.6     # 面向用户的真实成本指标
  max_contact_force_n: 22
```

**三条纪律**

1. **初值用随机化分布，不用「友好摆放」**：很多 demo 的失败是「今天杯子摆在训练时那个位置」。
2. **失败要分类统计**：`slip / wrong target / stuck / timeout / 安全停止 / 机械故障`。分类清楚才知道该修数据还是修控制。
3. **版本可比性**：同一协议 + 同一随机种子集（或同一初值列表文件），换模型才可比。评估集变化要在 changelog 里记录。

## 💻 统计与可视化：成功率不要只报一个数

```python
import numpy as np
from statsmodels.stats.proportion import proportion_confint   # 或自己写 Wilson

def report(succ, n, label):
    lo, hi = proportion_confint(succ, n, method="wilson")
    print(f"{label:22s} {succ:3d}/{n:<3d} = {succ/n:.0%}  95%CI[{lo:.0%},{hi:.0%}]")
    return succ/n, lo, hi

for cond in ["seen_obj", "new_obj", "new_scene", "new_cam", "night_light"]:
    s, n = results[cond]
    report(s, n, cond)          # 留出维度上的衰减一目了然

# 过程指标比结果指标更早暴露问题
print(pd.DataFrame(trials).groupby("model_version")[
    ["partial_credit", "median_seconds", "safety_stop", "human_resets"]].mean())
```

> ✅ **最佳实践**：把「衰减率」（新场景成功率 ÷ 已知场景成功率）当成一等指标。一个 90%→88% 的模型，通常比 95%→45% 的模型更适合上线。

## 📦 工程现场笔记

- **真机评测的组织成本极高**：需要人复位、复位要可复现（物体姿态用夹具 + 记录）、要录像留证。投资一个「自动复位台 + 相机标定板 + 一键评测脚本」比多买一条臂更划算。
- **录像与遥测一起存**：事后复盘缺了力/电流曲线，就只能靠视频猜原因。对齐时间戳的日志能省掉几周的争论。
- **回归测试要进 CI**：每次改动（模型、prompt、动作尺度、相机裁剪）都跑一轮「仿真 + 小样本真机」，防止「修 A 崩 B」。这与数字 Agent 的评估门禁同构，见 [持续评估](../11-engineering/continuous-evaluation.md)。
- **报告里要写「不做的任务」**：模型在哪些类别上失败被排除在评测外，是评审最关心的问题（对应数字侧的「评测集泄漏」）。
- **人形/机械臂的噪声、发热、电池衰减会影响分数**：评测要覆盖工作时长（第 1 小时与第 3 小时），必要时记录温度。

## ⚠️ 常见误区

- ❌ 「挑最好的 20 次报成绩」：等于把成功率当剪辑技巧
- ❌ 允许无限重试却仍叫「成功率」：重试次数要计入，或改成「有限重试下的完成率」
- ❌ 只报单一数字：不说 n、不说初值分布、不说是否人工干预 → 无法复现也无法对比
- ❌ 用仿真指标当验收：仿真能评「相对提升」，不能评「能不能上线」
- ❌ 不做安全/破坏性测试就进共融场景：能力测试全过 ≠ 通过现场安全评审
- ❌ 把「零样本」写进标题却悄悄做了微调：明确标注是 zero-shot / few-shot / fine-tuned

## 🧪 小练习

给你现在正在做的任务写一份 `eval_protocol.yaml`（含 4 个留出维度、每维 ≥20 次、失败分类表），然后跑一次并把结果贴给同事，问一句：「照这份文档，你能不能独立复现？」——凡是答不上来的，就是文档要补的地方。

## 🔗 相关资源

- [CALVIN](https://github.com/mees/calvin)、[LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO)、[SimplerEnv](https://simpler-env.github.io/)、[BEHAVIOR-1K](https://behavior.stanford.edu/)、[ManiSkill3](https://github.com/haosulab/ManiSkill)
- 方法层：[评估指标](../10-evaluation-safety/evaluation-metrics.md)、[基准测试](../10-evaluation-safety/benchmarks.md)、[可观测性与评估平台](../16-ai-infrastructure/llm-observability-eval-platform.md)

## 📚 相关知识点

- [仿真与 Sim-to-Real](simulation-sim2real.md)
- [数据引擎](data-engine.md)
- [硬件、实时与安全](hardware-realtime-safety.md)
