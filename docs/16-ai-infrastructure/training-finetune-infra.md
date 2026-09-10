---
tags: [infrastructure, llm, advanced]
type: knowledge
status: published
updated: 2026-09-10
---

# 训练与微调基础设施

> **一句话**：Agent 项目里的「微调」八成不是炼丹，而是流水线工程：数据配比、LoRA 适配器管理、可复现实验记录、断点续训、评估门禁、一键上线到推理引擎——把这六件事自动化，微调才划算。
> **难度**： 高级
> **标签**：`#infrastructure` `#llm`

## 先看结论

- **先分清你要什么**：行为风格/格式（→ LoRA 微调足够）、领域知识与事实（→ 优先 RAG，别指望权重记事实）、工具调用可靠性（→ SFT + 约束解码，往往不需要大改）。
- **LoRA / QLoRA 把门槛打到单机**：LoRA 只训低秩增量适配器；QLoRA 用 4-bit 量化底座 + LoRA，让 7B–70B 级模型在单卡/少数卡上可训。适配器可热插拔，多租户「一底座多适配器」是标准部署形态。
- **全参训练是分布式问题**：数据并行（DDP/FSDP）、张量并行、流水并行、专家并行——组合起来才塞得下大模型；框架层面常见 PyTorch FSDP、DeepSpeed、Megatron-LM 系。
- **RL/DPO 是「双模型在线」架构**：策略模型 + 参考模型（+ 奖励模型 / 判分器）同时驻留，还要有采样（rollout）用的推理引擎。训练与推理共享 GPU 池时，显存与调度冲突必须提前设计。
- **评估门禁比训练本身重要**：没有「不过就不上线」的评估集与阈值，微调会变成定期退化。

## 流水线全景

```mermaid
flowchart LR
  D[数据管线<br/>清洗/去重/配比] --> S[训练<br/>LoRA / FSDP / DeepSpeed]
  S --> C[Checkpoint + 实验记录<br/>config/commit/数据版本]
  C --> E[离线评估<br/>任务集 + 回归门禁]
  E -- 通过 --> A[适配器注册<br/>版本/底座/评测分]
  A --> V[推理引擎热加载<br/>vLLM/SGLang 多 LoRA]
  V --> P[线上影子/A-B]
  P -- 指标回退 --> R[一键回滚]
  E -- 不通过 --> D
```

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

```python
# 训练：peft + 4-bit 底座（QLoRA 思路）
from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
                          TrainingArguments, Trainer)
from peft import LoraConfig, TaskType, get_peft_model
import torch, json

bnb = BitsAndBytesConfig(load_in_4bit=True,
                         bnb_4bit_compute_dtype=torch.bfloat16,
                         bnb_4bit_quant_method="nf4")
tok = AutoTokenizer.from_pretrained("your-base-model")
model = AutoModelForCausalLM.from_pretrained(
    "your-base-model", quantization_config=bnb, device_map="auto")

lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                  target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                  task_type=TaskType.CAUSAL_LM)
model = get_peft_model(model, lora)
model.print_trainable_parameters()          # 通常 <1% 参数可训

ds = [json.loads(l) for l in open("sft.jsonl")]     # {"messages": [...]}
args = TrainingArguments(
    output_dir="out/lora-$(date +%s)",
    per_device_train_batch_size=1, gradient_accumulation_steps=16,
    learning_rate=2e-4, num_train_epochs=3,
    bf16=True, save_strategy="steps", save_steps=100, save_total_limit=3,
    logging_steps=10, seed=42,
)
# Trainer(train_dataset=..., args=args, model=model, processing_class=tok).train()
```

```bash
# 上线：vLLM 多 LoRA 热挂载，不改底座副本
vllm serve your-base-model --enable-lora \
  --lora-modules agent-v3=/mnt/adapters/agent-v3 \
  --max-loras 4 --max-lora-rank 32
# 请求侧只换 model 名即可切换适配器
curl :8000/v1/chat/completions -d '{"model":"agent-v3","messages":[...]}'
```

> 💡 **提示**：QLoRA 训练出的适配器上线前，要把 merge 与否想清楚——合并进底座（merge_and_unload）省推理开销但失去热切换能力；不合并保留多适配器路由能力。

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

## 相关资源

- [PEFT / LoRA](https://github.com/huggingface/peft)、[DeepSpeed](https://github.com/deepspeedai/DeepSpeed)、[PyTorch FSDP](https://pytorch.org/docs/stable/distributed.fsdp.html)、[Megatron-LM](https://github.com/NVIDIA/Megatron-LM)
- [TRL（SFT/DPO/PPO 一体）](https://github.com/huggingface/trl)、[OpenRLHF](https://github.com/OpenRLHF/OpenRLHF)
- 训练侧原理：[预训练、微调与指令微调](../03-llm/pretraining-finetuning.md)、[RLHF、DPO 与对齐](../03-llm/rlhf-dpo-alignment.md)

## 相关知识点

- [GPU 调度与多租户](gpu-scheduling-multitenancy.md)
- [数据与检索基础设施](data-vector-storage.md)
- [持续评估](../11-engineering/continuous-evaluation.md)
- [推理经济学与部署形态](inference-economics-deployment.md)
