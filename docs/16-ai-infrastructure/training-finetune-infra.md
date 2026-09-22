---
tags: [infrastructure, llm, advanced]
type: knowledge
status: published
updated: 2026-09-23
---

# 训练与微调基础设施

{% hint style="info" %}
**一句话**：Agent 项目里的「微调」八成不是炼丹，而是流水线工程：数据配比、LoRA 适配器管理、可复现实验记录、断点续训、评估门禁、一键上线到推理引擎——把这六件事自动化，微调才划算。
  **难度**： 高级
{% endhint %}

## 先看结论

- **先分清你要什么**：行为风格/格式（→ LoRA 微调足够）、领域知识与事实（→ 优先 RAG，别指望权重记事实）、工具调用可靠性（→ SFT + 约束解码，往往不需要大改）。
- **LoRA / QLoRA 把门槛打到单机**：LoRA 只训低秩增量适配器；QLoRA 用 4-bit 量化底座 + LoRA，让 7B–70B 级模型在单卡/少数卡上可训。适配器可热插拔，多租户「一底座多适配器」是标准部署形态。
- **全参训练是分布式问题**：数据并行（DDP/FSDP）、张量并行、流水并行、专家并行——组合起来才塞得下大模型；框架层面常见 PyTorch FSDP、DeepSpeed、Megatron-LM 系。
- **RL/DPO 是「双模型在线」架构**：策略模型 + 参考模型（+ 奖励模型 / 判分器）同时驻留，还要有采样（rollout）用的推理引擎。训练与推理共享 GPU 池时，显存与调度冲突必须提前设计。
- **评估门禁比训练本身重要**：没有「不过就不上线」的评估集与阈值，微调会变成定期退化。

## 流水线全景

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#E8F6ED","primaryBorderColor":"#16A34A","primaryTextColor":"#1F2937","secondaryColor":"#CCEBD7","tertiaryColor":"#F6FBF8","lineColor":"#7FCC9B","actorBkg":"#ECF8F1","actorBorder":"#16A34A","actorTextColor":"#1F2937","signalColor":"#5CBF80","noteBkgColor":"#D5EEDE","noteBorderColor":"#16A34A","noteTextColor":"#1F2937","labelBoxBkgColor":"#E8F6ED","labelBoxBorderColor":"#16A34A"}}}%%
flowchart LR
  D[数据管线<br/>清洗/去重/配比] --> S[训练<br/>LoRA / FSDP / DeepSpeed]
  S --> C[Checkpoint + 实验记录<br/>config/commit/数据版本]
  C --> E{离线评估<br/>回归门禁}
  E -- 不通过 --> D
```

*《图：离线侧——训练与准入闭环，离线评估与回归门禁不过就回炉重训，通过才拿到上线资格》*

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#E8F6ED","primaryBorderColor":"#16A34A","primaryTextColor":"#1F2937","secondaryColor":"#CCEBD7","tertiaryColor":"#F6FBF8","lineColor":"#7FCC9B","actorBkg":"#ECF8F1","actorBorder":"#16A34A","actorTextColor":"#1F2937","signalColor":"#5CBF80","noteBkgColor":"#D5EEDE","noteBorderColor":"#16A34A","noteTextColor":"#1F2937","labelBoxBkgColor":"#E8F6ED","labelBoxBorderColor":"#16A34A"}}}%%
flowchart LR
  A[适配器注册<br/>版本/底座/评测分] --> V[推理引擎热加载<br/>vLLM/SGLang 多 LoRA]
  V --> P[线上影子/A-B]
  P -- 指标回退 --> R[一键回滚]
```

*《图：微调上线链路·在线侧——拿到资格之后：注册→热加载→影子/A-B，指标回退则一键回滚；准入判定来自上图的离线闭环》*

## 选型对照

| 目标 | 方法 | 数据量级 | 算力量级 | 备注 |
|---|---|---|---|---|
| 输出格式稳定（JSON、话术） | SFT（LoRA） | 500–5k 条 | 单卡数小时 | 常见首选，先试这个 |
| 领域术语与风格 | SFT + 持续数据飞轮 | 5k–100k 条 | 多卡 | 与提示词/工具描述同步迭代 |
| 事实知识 | RAG（→ [记忆与 RAG](../06-memory-rag/rag-basics.md)） | — | 推理侧 | 权重记事实易过时、不可溯源 |
| 拒答/安全边界 | DPO / 偏好优化 | 数千偏好对 | 多卡 | 需要严格对照评估，防止「过度顺从」 |
| 复杂推理策略 | RL（GRPO/PPO 类）+ 可验证奖励 | 任务 + 判分器 | 数十卡起 | 只有奖励客观可验证（代码、数学、工具结果）时才值得 |
| 小模型专项替代大模型 | 蒸馏（教师输出造数据）+ SFT | 10k–200k 条 | 多卡 | 单位成本最优路径之一（→ [推理经济学](inference-economics-deployment.md)） |

## 六件必须自动化的事

1. **数据版本化**：训练集写成 manifest（文件哈希 + 条数 + 配比 + 来源许可），一次训练只跑一个 manifest 的快照，禁止「本地攒 jsonl」。
2. **可复现实验记录**：commit hash、镜像 digest、seed、超参、数据 manifest 一起入库（MLflow / W&B / 自家 table 都行，别用「我记得是 3e-5」）。
3. **Checkpoint 与断点续训**：按步数或时间落盘 + 保留最近 N 个；多机训练务必支持「从任一节点集合恢复」。Spot/抢占环境里没有这个就是烧钱。
4. **评估门禁**：固定任务集（30–200 例足够），跑一次 ≤30 分钟，指标不达标直接 fail CI。同时必须跑「回归集」：你原来能做的事不能因为微调坏了。
5. **适配器注册与灰度**：适配器即产物（底座 + LoRA 权重 + 评测分 + 责任人），推理引擎按需挂载；先影子流量（同一请求同时打旧/新模型，只记录不返回），再按租户灰度。
6. **回滚**：一行配置切回上一个适配器或基座模型；回滚时间目标 < 5 分钟，比训练快更重要。

## 最小可跑的 LoRA 微调 + 上线

不用背训练脚本，但要看得懂一个训练任务的**配置契约**：不管是 TRL、DeepSpeed 还是 LLaMA-Factory 系启动器，接受的都是一份同形状的声明式配置。下面是一个单机 QLoRA 任务的全量参数，开训时这份文件会连同 commit hash、镜像 digest、seed 一起进实验追踪（MLflow / W&B / 自家 table 都行）——**可复现靠这份文件，不靠「我记得是 3e-5」**：

```yaml
# 一次训练 = 一份配置快照；禁止「本地攒 jsonl、参数靠记忆」
base_model: your-base-model
quantization:                # QLoRA：4-bit 底座，把 7B–70B 级模型拉回单卡/少数卡可训
  load_in_4bit: true
  bnb_4bit_compute_dtype: bfloat16
  bnb_4bit_quant_method: nf4
peft:                        # 只训低秩增量适配器，可训参数通常 <1%
  task_type: CAUSAL_LM
  r: 16
  lora_alpha: 32             # 常用约定 alpha = 2 × r
  lora_dropout: 0.05
  target_modules: [q_proj, k_proj, v_proj, o_proj]   # 只挂注意力四个投影
dataset:
  path: sft.jsonl            # 每行 {"messages": [...]}，与推理请求同形状
training:
  output_dir: "out/lora-<unix时间戳>"    # 一次训练一个目录，不覆盖旧产物
  device_map: auto                       # 多卡时自动摆放
  per_device_train_batch_size: 1
  gradient_accumulation_steps: 16        # 单卡有效 batch = 1 × 16 = 16
  learning_rate: 2.0e-4
  num_train_epochs: 3
  bf16: true
  save_strategy: steps
  save_steps: 100
  save_total_limit: 3        # 只留最近 3 个 checkpoint，断点续训靠它们
  logging_steps: 10
  seed: 42
```

四个数字最容易被看漏：**有效 batch 是 16 不是 1**，梯度交流存换稳定；**`save_steps: 100` 与 `save_total_limit: 3` 是一对**，缺了这对，Spot 抢占一次就白训一截；**`seed: 42` 不是仪式感**，是为了让两个人跑出同一个分数；**`2e-4` 是 LoRA 的量级**，比全参微调高一个数量级，拿全参学习率来训 LoRA，loss 第一epoch 就飞。

## 从训练到上线：五步，每步带失败原因

{% stepper %}
{% step %}

#### 第 1 步：数据准备——先写 manifest，再谈训练

训练集落成 manifest（文件哈希 + 条数 + 配比 + 来源许可），SFT 通常 500–5k 条就够（见上文选型对照）。三件事必做：**与评估集去重**——重叠样本会让分数虚高，评估直接失效；**失败轨迹保留 10–30%**——只喂成功样本的模型遇到第一个错误就懵；**`messages` 形状与线上推理请求一致**——训练用的 chat template 和上线差一行，格式合法率就会在上线当天崩掉。

{% endstep %}

{% step %}

#### 第 2 步：训练——按配置契约执行，不凭手感改参

照上面那份 yaml 跑：`nf4` 4-bit 底座 + `bfloat16` 计算，四个 `q/k/v/o_proj` 可训，`lr=2e-4`、3 个 epoch、有效 batch 16，单卡数小时量级。每 `logging_steps: 10` 步看一眼 loss：若第 3 个 epoch 后段 loss 抬头，就在最近的 `save_steps=100` 检查点处停手、单独评估那一版，而不是训完再说——checkpoint 只留 3 个，晚发现就没了。

{% endstep %}

{% step %}

#### 第 3 步：评估门禁——新能力 + 回归，两套一起跑

固定任务集 30–200 例足够，一次跑完必须 ≤30 分钟，否则 CI 里没人愿意跑。两套集子缺一不可：**新能力集**（你训的事成了没有）和**回归集**（原来会的事坏没坏——工具调用格式、拒答边界最有代表性）。两条硬约束：阈值必须**高于噪声地板**（同一模型同一数据跑两遍的分数差就是地板）；评估必须在**上线配置**下跑——训练用 bf16、上线用 FP8/INT4 却不重测，等于裸奔。不过就回第 1 步修数据，而不是去改阈值。

{% endstep %}

{% step %}

#### 第 4 步：适配器注册——产物不是一个目录，是一条记录

底座 digest、适配器路径、评测分（新能力 + 回归两列）、责任人、merge 决策，五样一起入库。merge 决策这步绕不开：合并进底座（`merge_and_unload`）省推理开销但失去热切换；不合并且保留多适配器路由——同一个底座服务多个租户。注册表里写清选了哪种，否则半年后没人解释得了「这版为什么切不动」。

{% endstep %}

{% step %}

#### 第 5 步：上线——一个底座热挂多个适配器，请求只换 model 名

vLLM/SGLang 多 LoRA 热挂载，底座副本零改动：

```json
{
  "server": {
    "engine": "vLLM",
    "base_model": "your-base-model",
    "enable_lora": true,
    "lora_modules": { "agent-v3": "/mnt/adapters/agent-v3" },
    "max_loras": 4,
    "max_lora_rank": 32
  },
  "route": {
    "endpoint": ":8000/v1/chat/completions",
    "switch_key": "model",
    "example": { "model": "agent-v3", "messages": ["…"] }
  }
}
```

三个字段决定上线行为：`max_loras: 4` 表示同时常驻 4 个适配器，第 5 个租户的请求要现场加载、延迟会抖；`max_lora_rank: 32` 必须 ≥ 训练时的 `r: 16`，配小了适配器直接加载失败（报错信息还很隐晦）；请求侧只改 `model` 字段就完成切换——这就是灰度的实现方式：新旧适配器同时常驻，切流量只是改一个字段。先影子流量（同一请求同时打旧/新模型，只记录不返回），再按租户灰度；回滚 = 把 `model` 切回上一版名字，目标 < 5 分钟，比训练快更重要。

{% endstep %}
{% endstepper %}

## 门禁不过的三种结局（点标签切换）

{% tabs %}
{% tab title="新能力不达标" %}
评测分与底座持平。先别怀疑「模型学不会」，先怀疑**数据**：500 条对窄场景都嫌少，泛化自然差；补到 2k–5k 条再谈调参。第二顺位才是把 `r: 16 → 32`——适配器容量翻倍，表达力强了但小数据上过拟合更快，看 train/eval 分叉再决定，不要一步跳到调大 r。
{% endtab %}

{% tab title="回归集失败" %}
新能力过了，工具调用格式合法率却掉了、或拒答率变了——原来会的事被做坏了。原因几乎总在**数据配比**：领域数据占比过高，通用与工具轨迹行为被稀释。回炉重训改配比；最不该做的是把回归集里「太严的几例」删掉——那是自欺，下次退化没人报警。
{% endtab %}

{% tab title="分数抖动没法判" %}
这版高 0.01、下版低 0.02，红灯天天亮。把同一模型同一数据跑两遍，**差值就是噪声地板**：门禁阈值低于它，工程师很快学会忽略红灯——定期退化就是这么开始的。要么把阈值抬到噪声地板之上，要么把评估集扩到 200 例压方差，也别一次扫 30 个超参却没有固定评估协议——那只是随机走了 30 遍，赢的那个仍是过拟合。
{% endtab %}
{% endtabs %}

{% hint style="tip" %}
QLoRA 训练出的适配器上线前，要把 merge 与否想清楚——合并进底座（`merge_and_unload`）省推理开销但失去热切换能力；不合并保留多适配器路由能力。判据就一条：这个适配器是给「全量流量」用的，还是给「某个租户」用的。
{% endhint %}

## 工程现场笔记

- **RL 环境复用推理引擎**：主流开源 RL 框架的做法是「采样用 vLLM/SGLang，训练用 FSDP/Megatron」，两者分时或分池用同一批卡。工程难点在权重同步与显存腾挪，而不是算法。
- **奖励来自可验证任务**：代码执行结果、单测通过、格式校验、工具调用返回码。用 LLM-as-judge 当奖励要配双判分 + 定期人评，否则会被「讨好判分器」的策略钻空子。
- **数据配比是隐形超参**：通用语料:领域:工具轨迹（ReAct 轨迹含失败样本）的比例明显影响泛化；失败样本保留 10–30%，只喂成功轨迹的模型遇到错误就懵（对照 [错误恢复](../07-planning/README.md)）。
- **别用微调替代工具描述**：工具选不对，先修 description 与 schema（→ [工具注册中心](../11-engineering/tool-registry.md)），成本比训一版模型低两个数量级。

## 常见误区

- ❌ 「知识不足就微调」：微调提升的是行为分布，事实类知识仍然会编——要引用就给检索
- ❌ 数据没去重就训：与评估集重叠的样本会让分数虚高，评估直接失效
- ❌ 只评新能力不评回归：微调后工具调用格式坏掉、拒答率变化，这些都要有对照集
- ❌ 一次训 30 个超参但没有固定评估协议：你只是随机走了 30 遍，赢的那个还是过拟合
- ❌ 训练用 bf16、上线用 FP8/INT4 却不重测：量化会改变行为，评估必须在**上线配置**下跑

## 小练习

为你的 Agent 挑一个「微调可解、prompt 解决不了」的窄任务（例如工具参数命名规范、特定 SQL 方言、公司内部工单格式），构造 500 条 SFT 数据 + 50 条 held-out，做一次「底座 vs LoRA」对照，看命中率与格式合法率各变化多少。达不到 2 倍收益就别上线这一版。

## 参考资料

- [PEFT / LoRA](https://github.com/huggingface/peft)、[DeepSpeed](https://github.com/deepspeedai/DeepSpeed)、[PyTorch FSDP](https://pytorch.org/docs/stable/fsdp.html)、[Megatron-LM](https://github.com/NVIDIA/Megatron-LM)
- [TRL（SFT/DPO/PPO 一体）](https://github.com/huggingface/trl)、[OpenRLHF](https://github.com/OpenRLHF/OpenRLHF)

## 相关知识点

- [GPU 调度与多租户](gpu-scheduling-multitenancy.md)
- [数据与检索基础设施](data-vector-storage.md)
- [持续评估](../11-engineering/continuous-evaluation.md)
- [推理经济学与部署形态](inference-economics-deployment.md)
- [预训练、微调与指令微调](../03-llm/pretraining-finetuning.md)
- [RLHF、DPO 与对齐](../03-llm/rlhf-dpo-alignment.md)
