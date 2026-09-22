---
tags: [resource, evaluation]
type: index
status: published
updated: 2026-09-22
---

# 数据集

{% hint style="info" %}
**一句话**：Agent 训练与评估数据集索引。挑数据集先看三件事：许可证能不能用、有没有可能已进模型训练集（污染）、指标是怎么算出来的。
{% endhint %}

## 常用数据集速查

| 数据集 | 用途 | 链接 |
|---|---|---|
| SWE-bench 任务集 | 编程 Agent 评估（2294 真实 issue） | <https://www.swebench.com/> |
| WebArena 网站 + 任务 | 网页 Agent 评估环境 | <https://webarena.dev/> |
| GAIA 验证集 | 通用助理评估（Hugging Face 托管） | <https://huggingface.co/datasets/gaia-benchmark/GAIA> |
| ToolBench API 语料 | 工具调用训练/评估（1.6 万 API） | <https://github.com/OpenBMB/ToolBench> |
| AgentBench 环境 | 八场景综合评估 | <https://github.com/THUDM/AgentBench> |
| ALFWorld | 具身指令任务（Reflexion 等论文用） | <https://alfworld.github.io/> |
| WebShop | 网购任务环境（ReAct 论文用） | <https://webshop-pnlp.github.io/> |
| HotpotQA | 多跳问答（ReAct 论文用） | <https://hotpotqa.github.io/> |

## 后训练与预训练语料

许可与坑一栏写的是「用了会不会出问题」，不是官方条款摘要——真要上线，仍去数据集页读原文。

| 数据集 | 用途 | 许可与坑 | 链接 |
|---|---|---|---|
| LMSYS-Chat-1M | 100 万段真实多轮对话，看用户实际怎么问 | 申请制（HF 上需登录点同意，一般自动放行），卡片未标自由再分发许可。含真实用户信息，只适合做意图分布与安全分析，别直接拿去训要上线的模型 | <https://huggingface.co/datasets/lmsys/lmsys-chat-1m> |
| UltraChat | 合成多轮指令数据，SFT 起步料 | MIT，干净。清洗采样版用 <https://huggingface.co/datasets/HuggingFaceH4/ultrachat_200k> 更省事。合成对话的毛病是「太礼貌」，风格评测别用它 | <https://huggingface.co/datasets/stingning/ultrachat> |
| UltraFeedback | 多维偏好打分，训奖励模型的事实标准 | MIT。拿来即用直接上 binarized 版 <https://huggingface.co/datasets/HuggingFaceH4/ultrafeedback_binarized>；代价是 GPT-4 评审的偏好（长答、自信）已经写进标签里 | <https://huggingface.co/datasets/openbmb/UltraFeedback> |
| Anthropic hh-rlhf | helpful/harmless 人工偏好对比 | MIT，2022 年的老数据，标注口径偏保守，长度分布也歪；仍是理解 RLHF 数据长什么样的最快路径 | <https://huggingface.co/datasets/Anthropic/hh-rlhf> |
| OpenAssistant oasst1 | 35 种语言的树状人标对话 | Apache-2.0，商用无碍。项目早已停更，单条质量起伏大；真正的价值是那套多标注者树状协议设计 | <https://huggingface.co/datasets/OpenAssistant/oasst1> |
| GSM8K | 小学数学推理，自动判分 | MIT。答案唯一、最适合做 RL 奖励验证；也正因为太有名，主流模型基本都见过它——只当回归测试与训练动态探针，别当推理能力证据 | <https://huggingface.co/datasets/openai/gsm8k> |
| Tülu 3 SFT Mixture | 公开后训练配方的 SFT 混合数据 | ODC-BY，可商用但要按来源署名。同作者还有 <https://huggingface.co/datasets/allenai/Dolci-Instruct-SFT>。数据、配方、评测脚本一起放出，是目前复现成本最低的一份 | <https://huggingface.co/datasets/allenai/tulu-3-sft-mixture> |
| ToolACE | 8 万条可验证函数调用样本 | Apache-2.0。合成但带严格校验，比早期 Glaive/xlam 类干净；弱点同样在这里——全是「教科书式」调用，真实业务里的歧义参数、缺参追问它不覆盖 | <https://huggingface.co/datasets/Team-ACE/ToolACE> |
| SlimPajama-627B | 预训练语料，去重后 6270 亿 token | gated：需登录并在页面同意条款后才能下载，许可为开放数据协议而非无条件商用授权，落地前自查。同类可看 <https://huggingface.co/datasets/EleutherAI/pile>（许可标 other，混源且部分子集有版权争议）与 <https://huggingface.co/datasets/Skylion007/openwebtext>（社区镜像，标 CC0 但内容源自 Common Crawl 抽取，版权口径别说满） | <https://huggingface.co/datasets/cerebras/SlimPajama-627B> |

ShareGPT 一代的真人对话抓取（<https://github.com/domeccleston/sharegpt>）已随 API 抓取失效而停摆，镜像随时被下架且含未脱敏个人信息。今天还有论文用「原始 ShareGPT」训练，读到时可以直接怀疑其数据处理。

## 使用提示

- 评估用数据集注意**去污染**：确认未混入模型训练数据。GSM8K、HumanEval、HotpotQA 这三个是污染重灾区，分数异常高时先怀疑见过题
- 数据集卡片的 license 字段经常缺失或标错（LMSYS-Chat-1M 就没标），以页面正文与文件里的 LICENSE 为准
- 训练自己的 Agent 模型可参考 DeepSeek-R1 的蒸馏数据思路（[论文](https://arxiv.org/abs/2501.12948)）
- 构建领域内测集时借鉴这些数据集的任务定义与评分协议（→ [基准测试](../benchmarks/README.md)）
- 中文场景优先考虑 oasst1 / Tülu 3 这类带多语言的混合，纯英文指令集训出来的模型在中文里会明显更「不会追问」
