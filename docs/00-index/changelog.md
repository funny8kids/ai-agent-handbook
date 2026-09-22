---
tags: [index, changelog]
type: index
status: published
updated: 2026-09-22
---

# 更新日志

本页记录手册的结构调整与重要内容更新。

## 2026-09-22（第 21 次）全站 183 张图一次性离屏渲染 + 四条新审计轴：仍无可修缺陷

第 20 轮补了三页后，本轮先把「Mermaid 自然宽度 vs 正文列宽」这条主渲染轴从**逐页抽测**升级为**全站一次性实测**，再叠加四条没量过的结构轴去证伪。结论：**五路全绿，没有为凑指标而改的内容**；唯一变化是把这条更严的量测手段固化下来。

- **全局宽度回归：183/183 全部渲染成功，超宽 0 张**。把 `docs/`（除 14-templates）里全部 183 个 Mermaid 块抽进一张 HTML，用 Edge headless + 线上同版本 `mermaid@11.14.0` 一次性 `run` 渲染，逐块读回 SVG `viewBox` 宽：**0 块渲染失败**（等于全站解析器 0 失败的更强证据），**0 块 > 正文列宽 1120px**，最宽 **1116px**（12 章 README 的一条横向流水线），30 张落在 1000–1116px 的窄带内但均未越线。第 20 轮新增的三张（383 / 987 / 709px）在全局重测里依旧在阈内，**无超宽回归**。README 首页「最宽 1116px / 1120px」口径与本次实测**逐字吻合**。
- **B1 跨文件锚点失效：0（且此轴为空集）**。全站相对链接里 `](xxx.md#anchor)` 形态命中 **0 条**——本手册跨页引用一律指向文件、不带页内锚点，所以这条轴当前无可测对象；记下空集是为将来若引入 `#anchor` 时有基线。
- **B2 frontmatter 标签词表漂移：0**。抽出全站 `tags:` 用词做词频，新增三页沿用既有词（`llm/training/agents`、`engineering/safety/agents`、`rag/memory/advanced`），未引入孤儿新标签，四字段顺序 `tags→type→status→updated` 全站仍 **0 例外**。
- **B3 知识页房规小节缺失：0**。对 `type: knowledge` 页逐一核 `概念速查 / 常见误区 / 参考资料 / 相关知识点` 四段齐全，三张新页与既有页同样过关。
- **B4 SUMMARY 悬空条目：0**。`SUMMARY.md` 每条链接的目标 `.md` 均真实存在于 `docs/` 内容根内，无指向已删/改名文件的死条目。
- **量测手段自身的一个坑（记下来避免重跑）**：把 183 段 Mermaid 源码嵌进 HTML 时，源码里的 `<br/>`、`<`、`>` 会破坏 DOM、`&` 需转义；且聚合脚本里 `out.join('\n')` 若由 Python 三引号写出，会把 `\n` 变成**真换行**塞进 JS 字符串字面量 → 整段脚本语法错、连 STARTED 标记都不出现，表现为「0 张 SVG 渲染」的假阴性。两处都修好后 183/183 才如实渲染。
- **未做项 / 阻塞（诚实，与第 20 轮同）**：本轮**未改动任何页面内容**，仅新增此记录。第 17–20 轮的提交连同本轮**均只在本地**，尚未推上线——推送卡在 GitHub 交互式凭据（GCM）授权，只读 `git ls-remote` 可达、写 `git-receive-pack` 挂起，非代码问题。流程第 (5) 步「线上同步后抽查」对第 17–21 轮仍未闭环，需操作者本地执行一次 `git push origin main` 并在弹窗批准凭据后方可闭环。

## 2026-09-22（第 20 次）从「修缺陷」转向「补内容」：新增 3 张知识页，填三处真空

第 19 轮五轴全绿、无可修缺陷后，经操作者定方向，本轮**从缺陷自检转向内容增强**——这是产品级取舍，不是补漏。先做覆盖度扫描定位真空：`用轨迹微调 Agent`（全站 0 命中）、`Agent 失败模式图鉴/调试手册`（仅散见于可观测性页）、`RAG 检索质量调优`（rerank/混合检索/切块散在 5+ 页却无专页）。据此新增三页。

- **新增 3 页**：[用轨迹微调 Agent](../03-llm/agent-traj-finetuning.md)（轨迹定义与 loss masking、四种数据来源、SFT→拒绝采样→DPO/RL 三路线、工具泛化）、[Agent 失败模式图鉴与调试手册](../11-engineering/agent-failure-playbook.md)（六类失败按「症状→根因→对策」组织 + 分诊决策图）、[RAG 检索质量调优](../06-memory-rag/retrieval-quality-tuning.md)（切块→混合召回→重排→自我纠错→评估的调优漏斗）。
- **每张都过全套房规校验**：真解析器（mermaid 11.14.0，与线上同版本）逐块 `parse` **3/3 通过**；三张新图用 Edge headless 本地渲染实测自然宽度 **383 / 987 / 709px**，全部 < 正文列宽 1120px、无超宽回归，并截图目检确认章色正确（indigo/fuchsia/green）、文字无裁切；正文中文 **1729 / 1709 / 1551 字**，均远超 900 字门槛；每页 1 张带 `%%{init}%%` 章色 Mermaid + 图注、1 张提示卡、概念速查表、常见误区、参考资料。
- **引用零猜测**：三页共 18 条 arXiv 引用**逐条先 `curl` 取回页面真实 `<title>` 比对**再写入——过程中据此**剔除 1 条记错的编号**（`2407.14491` 实为无关的 3D 论文，非我以为的 ColPali），并纠正 `2005.11401` 是 RAG 原始论文（Lewis 2020）而非 DPR。
- **README 统计按实测增量对齐**（沿用第 17 轮「线上真会渲染」口径）：页 **187→190**、提示卡 **209→212**、Mermaid **180→183**、含参考资料页 **144→147**、读者可见图注 **162→165**、配图 **220→223**、去重一手来源 **316→324**；**含公式页 104 不变**（三页无 `$$`）。增量由脚本对「含/不含新页」两次点数之差得出，非手填。
- **导航接入**：三页已加入 `SUMMARY.md` 与各自章节导读列表，不制造站内孤儿。
- **未做项 / 阻塞（诚实）**：本轮三页 + 第 17/18/19 轮的提交**均已在本地，但仍未推上线**——推送卡在 GitHub 交互式凭据（GCM）授权，非代码问题；流程第 (5) 步「线上同步后抽查」对第 17–20 轮仍未闭环，需操作者本地 `git push origin main` 并批准凭据弹窗。

## 2026-09-22（第 19 次）五轴全绿的诚实记录：本轮没有可实测出的缺陷，但两笔提交卡在鉴权上没上线

按「找不到值得修的缺陷就汇报」的约定，这轮换 5 条**没量过的新轴**去证伪，结论是全部干净、**没有为凑指标而改的内容**。负结果也记，是为了让这些轴以后不必重复试。

- **A1 标题层级跳级：0**。逐页抽正文标题（剔除代码块），检查是否存在 `#`→`###` 这类跨级——全书 0 处，层级连续。
- **A2 跨页雷同 Mermaid：0**。把每个 Mermaid 块去掉分章配色指令后取哈希比对，没有两个页面共用一张「复制粘贴」图（≥40 字符的块），图不是凑数的。
- **A3 内容页残留占位符：0 真缺陷**。宽松扫 `TODO/FIXME/TBD/待补充/占位/xxx/lorem` 命中 31 处，收紧并排除合法用法后仅 2 处，且都是**在教写法的行内示例**（更新日志里描述 14 章负样本的 `` `xxx.svg` ``、Lab2 让读者「每条答案前缀『根据 xxx』」的引用占位范式）——无一是待填的坑。（宽松扫描之所以 31，是因为大小写不敏感把工具名 `TodoWrite`/`Todo 清单` 误配成 `TODO`，属口径噪声。）
- **A4 分章配色规范回归：180/180 全带 `%%{init}%%`**。第 14/27 轮压窄、改向 Mermaid 时有可能丢指令，实测**没有任何一个 Mermaid 块缺失章色指令**。
- **A5 代码围栏语言标注：0 个裸围栏**。非模板内容页里 ```` ``` ```` 开头块全部带语言标签，GitBook 高亮不会退化。
- **未做项 / 阻塞（诚实）**：第 17、18 轮的两笔提交（`49d1c05`、`10c5da7`）**已在本地，但尚未推上线**——推送卡在 GitHub 交互式凭据（GCM）授权，只读 `git ls-remote` 可达、写 `git-receive-pack` 挂起，非代码问题。因此第 17–19 轮流程第 (5) 步「线上同步后抽查」仍未完成，需操作者本地执行一次 `git push origin main` 并在弹窗批准凭据后方可闭环。本轮**未改动任何页面内容**，仅新增此记录。

## 2026-09-22（第 18 次）链接的「语义正确」：一次站内链接体检，只抓到一条真缺陷但把它坐实了

第 17 轮清完外链，这轮把**站内链接与页面结构**拆成 5 条新轴量：站内链接目标/锚点、`相关知识点` 双向性、中文字数密度、孤儿页、SUMMARY 收录，以及一处中文排版扫描。结论是——**大部分报警都是口径问题，不是内容缺陷**，只有 1 条是真要修的，但正因为用了能证伪的量测才没漏掉它。

- **唯一真缺陷：一处跳出 GitBook 内容根的链接**。[更新日志](./changelog.md) 里「门面升级」那条写 `[仓库首屏](../../README.md)`——从 `docs/00-index/` 出发，`../../README.md` 落到**仓库根**那份 README，而 GitBook 的内容根是 `docs/`，这份文件根本不在站上，线上读者点过去就是 404。改成指向仓库在 GitHub 上的地址 `https://github.com/funny8kids/ai-agent-handbook`（该 URL 由 `git remote` 得出并经 GitHub API `200` 核验，非猜测），句子也补了一句「在 GitHub 上，不在站内 `docs/` 内容根里」，让读者知道点出去会离开本站。量测脚本断言：改后 `docs/` 内**跳出内容根的相对链接 0 条**。
- **14-templates 的 2 条"断链"是故意的，不修**：[风格指南](../14-templates/style-guide.md) 的反面示范里写着 `../.gitbook/assets/xxx.svg` 与一个 `[标题](占位)` 示例，是用来教「别这么写」的**负样本**，被链接扫描如实报成 missing 属预期，按房规排除，不动。
- **一条被证伪的"轴"——不立它**：初版量了「`相关知识点` 是否双向」（X 列了 Y、Y 没回列 X），报出 324 处。但本手册的 `相关知识点` 本就是**向前指**的（把读者往更深的机制页/下一步引），双向对称是我凭空加的规则，不是全书约定；拿它当缺陷去"修"就是为凑指标改内容。**判据：新轴先问"这规则书里真有吗"，答案没有就退役，不拿它开工。**
- **其余全绿（且是"复测确认没退化"，不是自夸）**：站内锚点失效 **0**；`type: knowledge` 正文低于 900 中文字的 **0** 页（第 15 轮补到 ≥900 的成果稳住了）；无任何入链的真孤儿页 **0**；已发布页缺 `SUMMARY.md` 条目 **0**；中文排版扫描（弯引号不配对、重复标点、半角逗号夹在中文间、中英粘连缺空格）报出的 **7 处全是假阳性**——ASCII 逗号都在行内代码的 RDF 三元组 `(实体, 任职于, ACME)` 里、其余是 Markdown 链接语法与一处「描述旧错字」的引号示例，逐条看过无一该改。

## 2026-09-22（第 17 次）元数据与统计会不会骗人：把「最后更新」「README 数字」「外链健康」三件事重新量一遍

前 16 轮都在改页面本身，这一轮只查**关于页面的陈述是不是真的**——三条新轴（N=frontmatter 日期、S=README 统计、P=外链健康），每条都先量出偏差再改，不靠感觉。

- **N 轴·「最后更新」失真 79 页 → 0**：一次比对 `git log` 各文件末次提交日 vs frontmatter 的 `updated`，量出 **79 页**写着 09-20，实际当天有十余次提交（补图注、核引用、重排图形、增厚薄页）改过它们。全部回填为 09-22。先把口径写进[风格指南](../14-templates/style-guide.md)第八节并加进第九节检查清单：`updated` =「本页正文最后一次发生读者可见变化的日期」，改字/改图/改图注/改表格都算，只动脚本或 CI 不算。**一个诚实的前提也一并写清**：GitBook 页面右上角的「Last updated」用的是平台自身修订时间，仓库写什么都不影响它（已验证：某页 `updated` 写 09-20，线上仍显示 09-22）——所以这次回填不是为了骗读者，而是让仓库这份元数据能当真，维护者靠它判断「哪页多久没动过」。顺带给两份模板页（[知识页模板](../14-templates/knowledge-template.md)、[资源卡片模板](../14-templates/resource-template.md)）补上它们自己缺的 frontmatter，并把风格指南里「模板页免 frontmatter」的旧豁免改成准确表述（模板正文里那段 YAML 只是围栏示例，模板页本身该有真 frontmatter）。
- **S 轴·README 四处数字与实测不符 → 全部对齐**：脚本 `audit17s` 以「线上真会渲染」为口径重新点数（代码块、行内代码里的写法示例一律不计），量出并改正 README 首页四条：含公式页 **105→104**（有一页的 `$$` 只出现在代码块示例里，线上不渲染）、提示卡 **202→209**、去重后一手来源 **315→316**、配图 **222→220**（把「用作 GitBook 站标、不进正文的 2 张 SVG」从配图数里剔除并注明）。改完 README 的 **11 项统计全部与实测一致**（pages 187 / chapters 19 / formula 104 / hints 209 / mermaid 180 / captions 162 / ref-pages 144 / unique-sources 316 / projects 323 / figures 220 / labs 6）。
- **P 轴·694 条唯一外链复检：硬断 0**：16 路并发把全站外链走一遍，**P0（404/410/401/402）= 0**，无一条内容性死链。首轮有 77 条「无响应」，逐条降并发重探后 **43 条恢复 200**（全是 arxiv，首轮是被并发限流误判）；剩余 **34 条仍是连接层失败**（curl 7/28/35，即 TCP/TLS 连不上，`--max-time 40` 顺序重探与 `WebFetch` 两条独立通路结果一致），且**按主机聚集**：huggingface.co/*、sre.google、aws.amazon.com、reddit、news.ycombinator、mujoco.org、gist、discuss——是本沙箱的**出站网络屏蔽了这些站点**，不是页面死了。这 34 条全是规范里点名的一手来源（gsm8k、SlimPajama-627B、ToolACE、GAIA、bge-m3、mujoco、SRE book、AWS backoff），按「不为凑指标删内容」一律保留，只在此记录其不可达是环境所致。

- **回归校验**：188 个 md 文件 frontmatter **0 未闭合**、代码围栏 **0 不配对**、四字段齐全且顺序（`tags→type→status→updated`）**0 例外**；本次改动**未触碰任何 Mermaid 块**（脚本比对整份 diff，图相关行 0 条），故第 15/16 轮的「解析器 180 块 0 失败、最宽 1116px、竖排 9 张按定调保留」结论对本提交仍然成立、无需重跑；README 统计与实测 0 漂移。本轮 83 个文件、**+109 / −86 行**，其中 79 个文件仅改 `updated` 一行，正文信息**零删除**。

## 2026-09-22（第 16 次）图形有没有被解释：一条平台事实推翻了"图画得对就算完"

本轮的起点是一条**平台行为**：GitBook 渲染正文图片时会**剥掉 alt 文本**，读者在页面上根本看不到它；Mermaid 块更是没有 alt。也就是说前 15 轮里那些写得很好的 alt（「Open WebUI 真实界面：模型选择器、内联渲染的图表…」）对读者等于不存在。据此新建 5 条量测轴（资产健康 L1/L2、图注质量 M1–M5、裸图 F1–F3、图内说明缺失 D2'、章节内导航 I），每条都先用**假想反例**标定（该抓的抓到、不该抓的不抓）再上库。

- **32→1 处"读者看不到解释"的配图**：34 张自绘 SVG / 真实截图里有 32 张只有 alt 没有可见文字，现全部在图下补 `*《图：……》*`；剩 1 处是 `docs/README.md` 的首屏横幅，纯装饰、写进规范的豁免条款。补的是**图本身带不出的那句判断**，例：[仿真与 Sim2Real](../17-embodied-ai/simulation-sim2real.md) 的图注直接点出全章最该记住的数字——无随机化 95%→35%，只随机化视觉仍是 88%→52%，「动力学失配不会被更好的贴图救回来」。
- **99→0 张"裸图"**：180 个 Mermaid 块里 99 张既没有图注、上下也没有一句实质正文（多是紧跟标题出现的）。分 5 批由子 Agent 逐张读图后补写，再用重复度检测（M1）与空话尾缀检测（M2）复查：**重复图注 0 条、"…的流程图/示意图"式空话 0 条**。典型如[提示注入](../10-evaluation-safety/prompt-injection.md)——图注点明"泄漏那两步用的全是 Agent 自己合法的 tool call，攻击者没拿到任何权限，只是往页面返回值里塞了一句话"。现存图注 162 条（132 张 Mermaid + 30 处配图）。
- **48 张图判为"无需补图注"，并把这条规则写进规范**：新轴的第一版只回看**图前**有没有话，误报 6 张——那些图后面就跟着实质正文（如[对齐与安全](../10-evaluation-safety/alignment-safety.md) 图后的"为什么是环不是线：评估→约束→上线→监控→新行为回流成用例"）。把检测改成双向后 **F1/F2/F3 全为 0**。结论固化进[风格指南](../14-templates/style-guide.md)：Mermaid 不强制图注，但**必须被实质文字解释**（图前或图后皆可），而「如下图所示」「见下图」这类**换个图也成立的纯指针不合格**。
- **章节内导航缺口 5→0**：[贡献指南](../99-about/contributing.md) 与[许可证](../99-about/license.md) 此前互不引用（各自在站上孤着一页），现互相链上；[第 18 章目录页](../18-frontier-2026/README.md) 的页面表漏收了 [Computer Use 2026](../18-frontier-2026/computer-use-2026.md) 与 [评估 2026](../18-frontier-2026/eval-2026.md) 两篇——读者从章首页点不到它们，这是真缺口不是量测口径问题，已补两行「读完能做到」式的说明。
- **四条过期量测轴如实退役，不当成"缺陷清零"**：D2（400 字窗口内找图注）会对"用正文解释图"的页面重复计数，退役为 INFO，由更严的 D2' 接管；B2 的阈值原本写 5 条自测题，实测全书 15 个教学章**整齐地都是 3 条**（房规就是 3），阈值改 3——写错阈值测的是"和我不一样的地方"而不是缺陷；G1 原以为术语表页要按章号收录每章术语，实际总表是按主题分组、每章的中英对照在章末「本章术语速查」，改成 G1'（教学章缺该小节＝0）；K（无图注的 Mermaid 块 48）由上面的 F 轴取代。**留下的教训：每条轴都要能被假想反例证伪，也要能被真实语料证伪。**
- **回归校验**：180 块真解析器 `parsed=180 failed=0`；几何与第 15 轮**完全一致**（最宽 1116px、超宽 0、9 张竖条按操作者定调保留）；189 个 md 围栏配对 0 异常、frontmatter 不符房风格仍只有 1 个（截图清单 `MANIFEST.md`，有意保留）；站内链接 1532 条 0 断链；知识页 900 字以下仍为 0；图片资产 L1（引用了但不存在的图）0、L2（存在但没人引用的图）2 张是 GitBook 后台用的站点图标，属有意保留。本轮 118 个文件、**+270 行 / −4 行**（含本条 changelog 与统计行），除 4 行外全部是新增说明文字，未删任何内容。统计同步：`docs/README.md` 增加"162 条读者可见图注"一条。

## 2026-09-22（第 15 次）量测引擎与线上对齐：上一轮的图形结论有一半是错的

本轮第一个缺陷在**工具身上**：本地量测用的是 mermaid 12.0.0，而 GitBook 线上加载的是 `mermaid@11.14.0`（从页面 `<script>` 里读出来的）。两个版本对「`flowchart` 方向 × 互不相连 subgraph」的处理规则**正好相反**，所以第 14 轮那两条"实测规律"站不住。校准做法：抓一张线上已渲染页面的 SVG `viewBox`（497.52×1542.70），与本地同源码渲染结果比对，把本地降到 11.14.0 后得到 498×1543 才算对上。**教训固化为一条前置检查：量测引擎版本必须先证明与线上同版本，再谈规律。**

- **换引擎后同一批 170 块重测，缺陷清单完全变样**：超宽 **0→12 块**（最宽 1712px，线上等于把字缩到 10.4px），上一轮判定的 30 张「竖条」里只有 **14 张**在 11.14 下真的是竖条。也就是说第 14 轮"清零超宽"是本地自欺，线上从没清过。
- **11.14 下重新量出的排布规律**（已全部写进[风格指南](../14-templates/style-guide.md)）：① 宽度由**排数 × 每排节点数**决定，精简标签措辞几乎无效（1244→1174，约 5%），无损合并掉一排才有效（1158→999，约 160px）。② `flowchart TB` + 两个**互不相连**的 subgraph 才是「左右双栏、栏内横向」（1098×244）；同样的源码写 `flowchart LR` 会塌成 349×840 的竖条。③ TB 父图里 subgraph 的 `direction LR` 仍被忽略（加与不加都是 1060×244）。④ TB 父图下**后声明的 subgraph 渲染在左边**，源码顺序与读图顺序相反，图注写「左/右」必须截图复核。
- **超宽 12→0**：能无损并排的就并排——[安全边界](../17-embodied-ai/hardware-realtime-safety.md) 1433→999、[对齐与安全](../10-evaluation-safety/alignment-safety.md) 1410→1029（5 排压成 3 排）、[LangChain 一条链](../09-frameworks/langchain.md) 1206→966（终点节点合并）、[DSPy](../09-frameworks/dspy.md) 1238→1106；其余按 ① 处理或按下一条拆块。全库最宽 1712→**1116px**，180 块有效字号全部 16.0px（无任何缩放）。
- **竖条最严重的 9 张拆成上下两块**：[向量存储](../16-ai-infrastructure/data-vector-storage.md)、[微调基建](../16-ai-infrastructure/training-finetune-infra.md)、[结构化输出](../04-prompt-reasoning/structured-output.md)、[RAG 基础](../06-memory-rag/rag-basics.md)、[LlamaIndex](../09-frameworks/llamaindex.md)、[SWE-bench](../13-resources/benchmarks/swe-bench.md)、[MCP Servers](../13-resources/tools/mcp-servers.md)、[机器人基础模型](../17-embodied-ai/robot-foundation-models.md)、[实验地图](../19-labs/README.md)。被拆掉的跨块连线一律写进图注，信息不丢（例：向量存储的「反馈回流到清洗切块」）。块数 170→180（另 1 张是新增，见下）。
- **两张图有真实的图形完整性 bug**（新写的一版未命名节点 lint 抓出来的，该 lint 误报率太高已弃用，但这两条是真的）：[GoT](../04-prompt-reasoning/graph-of-thoughts.md) 的树图用裸 ID，线上渲染出写着「A1」「A2」的空盒子，现在全部补上标签并按 ④ 重排为 1098×244 的双栏；[Reflexion](../04-prompt-reasoning/reflexion.md) 有一条 `B2 --> C` 的边引用了不存在的节点，Mermaid 会凭空造一个空节点，已删。
- **正文厚度：900 字以下的知识页 7→0**。本轮补的是机制不是字数：[Self-Refine](../04-prompt-reasoning/self-refine.md) 823→1097（反馈来源四档对照 + 选择规则）、[GoT](../04-prompt-reasoning/graph-of-thoughts.md) 837→1055（三种可落地的聚合算子）、[协议栈 2026](../18-frontier-2026/protocol-stack-2026.md) 843→949（判据反读）、[Semantic Kernel](../09-frameworks/semantic-kernel.md) 852→952（迁移成本三处）、[Reflexion](../04-prompt-reasoning/reflexion.md) 874→1014（复盘存哪一层、按失败签名去重）、[OpenAI Agents API](../18-frontier-2026/openai-agents-api.md) 895→958（可移植性要主动测）、[Swarm 交接](../08-multi-agent/swarm.md) 898→1140（一次合格交接的四个字段 + 验收法）。
- **提示卡一致性**：9 个索引页的开头引用块统一改成房风格 `{% hint style="info" %}` **一句话**卡（[总索引](../00-index/README.md)、[资源库](../13-resources/README.md) 下 7 个子索引、[许可证](../99-about/license.md)），文字只做改写与补足，不删信息。脚本对每条替换都断言命中唯一，FAILS: 0。
- **最后一张无图的大页补图**：[开源项目索引](../13-resources/projects/README.md)（3539 字，全库最大的无图页）新增「怎么用这张索引」三分类决策图。
- **上一轮自己造成的损伤，如实记**：第 14 次提交（`4e2d236`）误删了「第 13 次」小节标题，导致那一轮正文挂在第 14 次底下。本轮从 `319412c` 取回原文恢复。
- **回归校验**：180 个 Mermaid 块真解析器 `parsed=180 failed=0`；188 页 0 断链、0 孤儿页、0 页缺 SUMMARY 条目、0 锚点失效；189 个 md 围栏配对 0 异常；frontmatter 不符房风格仍只有 1 个（截图清单 `MANIFEST.md`，有意保留）；统计同步为 README 的 Mermaid 180 / 配图 222 / 最宽 1116px。一个假阳性也记在这里：资产扫描把 `cover-handbook.svg` 报成"未使用"，实际它被仓库根目录 README 引用，是脚本只扫 `docs/` 的口径问题。
- **留下的取舍（要操作者定调）**：仍有 **9 张竖条**未拆——[WebArena](../13-resources/benchmarks/webarena.md) 347×734、[LangGraph](../09-frameworks/langgraph.md) 363×638、[OpenAI Agents API](../18-frontier-2026/openai-agents-api.md) 364×652、[AI 简史](../01-ai-basics/ai-history.md) 370×854、[越狱攻击](../10-evaluation-safety/jailbreak.md) 373×654、[人形机器人运动控制](../17-embodied-ai/humanoid-locomotion.md) 374×830、[工具注册表](../11-engineering/tool-registry.md) 388×504、[通用 Agent 产品](../12-applications/general-agent-products.md) 408×788、[企业知识库](../12-applications/enterprise-knowledge-base.md) 408×884。它们**字号都是满尺寸 16px，读起来不费力**，只是右侧留白多；而且这一批的纵向本身就是语义（时间轴、防御纵深、分层收敛），拆成两块会丢掉"一层压一层"的读法。要不要为版面整齐牺牲这层语义，属产品级取舍，本轮不动。**（2026-09-22 操作者定调：保留竖排，这 9 张结案。）** 其余未做项：14 个无图页全部是 `type: index` 索引页，按规范免图；[基准](../13-resources/benchmarks/README.md)、[数据集](../13-resources/datasets/README.md) 等 4 张表格型索引不为凑字数硬扩；封面/横幅两张 SVG 的自然宽 1600/1920px 是通栏素材，按设计豁免。

## 2026-09-22（第 14 次）正文厚度与图形几何：薄页、超宽图、细条图三类缺陷一起量清

这一轮沿用「先量后改」，并新增两条量纲：知识页正文的中文字数、每张 Mermaid 图的**自然宽×高比例**。上一轮只量了宽度，漏掉了反方向的毛病——图太窄也会毁排版。

- **薄页增厚 12 篇**：最低门槛 600 字、目标线 900 字。低于门槛的 4 篇全部改写：[语音 Agent](../12-applications/voice-agent.md) 424→1376、[Computer Use 2026](../18-frontier-2026/computer-use-2026.md) 362→997、[模型原生 vs Harness](../18-frontier-2026/model-native-vs-harness.md) 451→1365、[协议栈 2026](../18-frontier-2026/protocol-stack-2026.md) 397→902。另外 8 篇补的是机制而非字数：[第 18 章评测](../18-frontier-2026/eval-2026.md) 591→1141（里程碑打分式 + 任务 YAML 模板 + 归因纪律）、[Claude Agent SDK](../18-frontier-2026/claude-agent-sdk.md) →1356（resume/fork 成本式、三环境 `build_options()`）、[事故实录](../10-evaluation-safety/safety-incidents-2026.md) →1265（L0–L3 响应阶梯 + `gate_and_watch()` 伪代码）、[通用 Agent 产品](../12-applications/general-agent-products.md) →1029（验收件三件套 + 托付度公式）、[记忆类型](../06-memory-rag/memory-types.md) →1102（写入/检索/遗忘三操作与衰减打分式）、[角色分配](../08-multi-agent/role-assignment.md) →1073（`worker-artifact-v1` 交接契约、加角色的四问）、[ToT](../04-prompt-reasoning/tree-of-thoughts.md) →1128（预算不等式 `p_T − p_1 > λc(bd−1)`）、[CrewAI](../09-frameworks/crewai.md) →1096（sequential 成本来源与三个杠杆）。全库 900 字以下的知识页从 **19 篇降到 8 篇**；剩下 8 篇 823–898 字，逐篇核对房风格小节齐全（图、源码案例、误区、小练习、参考资料），再写就是凑数，保留原样。
- **超宽图 25→0**：把仍超出正文列宽的 25 张压回列内——LR 长链无损合并到 ≤5 排、扇形图去掉占位根节点、时序图折长消息并缩短参与者别名。全库最宽 1328→1096px。
- **本轮新发现的第二类图形缺陷：细条图**。宽度达标不等于排布合理：把每块的 W×H 一起量出来后，发现 **40 个块是「窄高细条」**（W<420 且 H>380，宽高比 <0.55），线上表现为正文右侧一大片空白。已改造比例最差的 10 张：[MCP Servers 目录](../13-resources/tools/mcp-servers.md) 252×1342→990×533、[微调基建](../16-ai-infrastructure/training-finetune-infra.md) 256×1096→862×516、[结构化输出](../04-prompt-reasoning/structured-output.md) 364×1372→1014×626、[SWE-bench](../13-resources/benchmarks/swe-bench.md) 360×1236→896×611、[向量存储](../16-ai-infrastructure/data-vector-storage.md) 376×1248→956×568、[RAG 基础](../06-memory-rag/rag-basics.md) 304×974→1096×342、[LlamaIndex](../09-frameworks/llamaindex.md) 328×1022→744×438、[动手实验地图](../19-labs/README.md) 168×936→568×470、[角色分配](../08-multi-agent/role-assignment.md) 244×664→1056×112、[第 18 章评测](../18-frontier-2026/eval-2026.md) 360×686→982×219。
- **两条实测出来的 Mermaid 排布规律**（已固化进[风格指南](../14-templates/style-guide.md)）：① `flowchart TB` 的长链必然塌成细条，而 `subgraph … direction LR` 在本 Mermaid 版本被忽略（实测仍渲染成 304×829 的竖排）；唯一有效的做法是父图改 `flowchart LR` 并让两个 subgraph **互不相连**——只要有一条跨排边，dagre 就把两排横向拼接（5 排链一拼就 1600px 以上），被删掉的跨排边改写进图注，信息不丢。② 父图为 LR 时**后声明的 subgraph 渲染在上面**，所以源码里要把逻辑上的第二排写在前面；本次 10 张图全部按此调序并逐张截图复核。
- **失败与回退如实记录**：曾按「最长路径 ≤5 就换 LR」批量翻转 16 张图，实测 **15 张超宽**（最高 2053px、字号被缩到 8.7px），已全部回退，只有第 18 章评测流水线一张成立。教训是 rank 数不等于最长路径——旁支与孤立节点各占一排，这条也写进了风格指南，避免下轮重犯。
- **一处真实错字**：[通用 Agent 产品](../12-applications/general-agent-products.md) 里「付款前停”」引号不配对，改为「付款前停止」。
- **回归校验**：170 个 Mermaid 块真解析器 `parsed=170 failed=0`（较上轮 +2：第 18 章评测流水线图、协议栈时序图），全树宽度复测 **0 超宽**、最宽 1096px、每块有效字号 16.0px；189 个 md 文件围栏配对 0 异常；frontmatter 不符房风格仅 1 个（`.gitbook/assets/screenshots/MANIFEST.md`，有意保留）；知识页缺「参考资料」0；站内链接 1484 条 0 断链，692 条唯一外链逐条核查 0 硬断。统计同步：README 的 Mermaid 168→170、配图 210→212、含公式页 100→105。
- **下一轮待办（需要操作者定调）**：仍有约 30 张图属「窄高细条」（比例 0.34–0.55，如[权限四层楼](../10-evaluation-safety/permission-sandbox.md) 348×1080、[CrewAI 流程](../09-frameworks/crewai.md) 296×1038、[AI 简史](../01-ai-basics/ai-history.md) 360×768）。其中一部分**纵向本身就是语义**（防御纵深、时间轴、层级收敛），拆成两排会丢掉「一层压一层」的读法；要不要为版面整齐牺牲这层语义，属产品级取舍，本轮不动。**（本条与上一条的宽度数字是用 mermaid 12.0.0 量的，与线上版本不一致，已在第 15 轮作废重测：11.14 下真竖条 14 张，拆掉 9 张、保留 9 张；2026-09-22 操作者定调——保留竖排，纵向是语义，版面整齐不值得用它换。今后时间轴/防御纵深/分层收敛类图形同样允许竖排，不再计入待修。）**



## 2026-09-22（第 13 次）出处体检：小节命名、站内链接错位与引用编号核对

前 12 轮都在补图和补内容，这一轮只查一件事：**书里写的出处，是不是真的、对不对得上**。量测方式全部可复现——脚本点数 + 逐条 curl + arXiv export API 比对标题，不用主观判断。结果比预想的糟：问题不在「没写引用」，而在「写了但用错了地方」。

- **一个小节被当两个用**：全库同名小节实际有三种状态——`## 参考资料` 101 篇、`## 相关资源` 26 篇（内容其实是站内跳转）、缺失 12 篇。26 处已全部统一改名为「参考资料」，再把混在里面的 **48 条站内链接**搬到「相关知识点」（21 个文件）。改完的口径是：**「参考资料」只放外部一手来源，站内跳转归「相关知识点」**，两条规则各有一个脚本断言把守（残留 0、混排 0）。
- **补齐真正缺一手来源的页面**：27 个正文页 + 10 个资源页/卡片新增已验证的一手来源（论文编号、官方仓库、协议文档、部署指南）。以「外部一手来源少于 3 条」为阈值，知识+资源页从 **40 篇降到 4 篇**——剩下 4 篇是 Toolformer 论文（官方未释出代码与权重）、Pi / DeepSeek Harness / MCP Servers 目录（一个仓库加一个官网就是它全部的官方入口），给它们挂二手转载才是灌水，故在卡片里写明原因、保留少于 3 条。
- **全站外链健康普查**：669 条唯一 URL 逐条走 16 路并发核查（GitHub 改用 API 绕开限流），**619 条返回 200**；硬断链 2 条已修：LangGraph 项目页里指向已下线的 `langgraph-templates` 仓库，改指官方公告 [Launching LangGraph Templates](https://www.langchain.com/blog/launching-langgraph-templates)；[游戏 Agent](../12-applications/game-agent.md) 里 OpenAI VPT 的研究页 403，改指 [官方仓库](https://github.com/openai/Video-Pre-Training)（两处标签同步改写，不保留对不上号的措辞）。
- **引用编号交叉核对（本轮最有价值的一项）**：把 104 个 arXiv 编号丢给 `export.arxiv.org` 取回真标题，再与标签逐条比对，抓出 **3 处错配**：[主流基准对比](../10-evaluation-safety/agentbench-webarena-swebench-gaia-toolbench.md) 把 SWE-bench 论文挂成了 WebArena 的 `2307.13854`（正解 `2310.06770`，另补 WebArena 自己的条目）；[知识图谱](../06-memory-rag/knowledge-graph.md) 标签写 TransE 却链到 word2vec 的 `1301.3781`（改 `1412.6575`，标题按 API 返回值改写为 *Embedding Entities and Relations…*）；[机器人基础模型](../17-embodied-ai/robot-foundation-models.md) 的 GO-1 标签补出论文真名（AgiBot World Colosseo）。另外差点写进一处新错：Toolformer 的 ACL 2023 会议版编号按记忆填会得到 `2023.acl-long.551`，点开才发现是另一篇表格问答论文，因此该卡片只保留 arXiv 一条。
- **frontmatter 与围栏**：11 个漏标文件补上（6 个实验 → `type: lab`，README/更新日志/贡献/许可 → `type: index`），[推理经济学](../16-ai-infrastructure/inference-economics-deployment.md) 那段无语言标注的公式围栏标成 ```text；不符合房风格（`tags → type → status → updated`）的文件从 15 个降到 3 个——`SUMMARY.md` 与 14 章两份模板示例，属有意保留。
- **规范固化**：[风格指南](../14-templates/style-guide.md) 第五节新增三条硬规则（命名唯一、≥3 条、每条都要实际点开且标题对得上，arXiv 用 export API 核对），资源卡片体裁说明与发布检查清单同步；[资源模板](../14-templates/resource-template.md) 里残留的「相关资源」表述改正。
- **回归校验**：189 个 md 文件围栏配对 0 异常，168 个 Mermaid 块真解析器 `parsed=168 failed=0`，无断链回归，187 页 / 19 章统计不变。
- **本机测不到的部分如实记录**：14 条未能拿到 200 的链接里，7 条是站点反爬 403（`openai.com`、`iso.org`、`dl.acm.org`、`academic.oup.com`、`platform.openai.com`、`wiki.linuxfoundation.org`、`developers.openai.com`），7 条是本机 DNS 被路由器劫持（`sre.google`、`huggingface.co`、`mujoco.org`、`hastie.su.domains` 全部解析到 `192.168.31.1` 后超时）——后者按「unreachable ≠ dead」处理，未删；其中 `sre.google` 两条经搜索引擎确认页面确实在线。**下一轮待办（已用体裁核对过，不是笼统的「补图补字」）**：19 篇知识页正文低于 900 字，其中 4 篇低于本书最低门槛 600 字（[Computer Use 2026](../18-frontier-2026/computer-use-2026.md)、[协议栈 2026](../18-frontier-2026/protocol-stack-2026.md)、[语音 Agent](../12-applications/voice-agent.md)、[模型原生 vs Harness](../18-frontier-2026/model-native-vs-harness.md)），优先增厚这 4 篇；15 个无图页面经逐一体裁核对全部是 `type: index` 的索引页，按规范本就免图，不再为凑指标硬塞。

## 2026-09-22（第 12 次）全库 Mermaid 宽度实测：把被线上缩小的图救回来

修完 Lab 2 那张图后顺手做了一次全库量测：用真 Mermaid 渲染 168 个块，逐块读 SVG 的 `viewBox` 自然宽度，和 GitBook 正文列宽（约 1120px）比对。**结论是这类缺陷不是个例：39 个块比正文列宽还宽**，线上被等比缩小后文字跟着变小——最糟的是[学习路线](../00-index/learning-path.md)那张 15 章横向链，自然宽度 2664px，缩到 42%，16px 的字只剩 **6.7px**，等于摆一张看不清的图。

- **改造 17 个最严重的块**（缩小后字号 ≤13.4px）：长链一律换轴（`flowchart LR` ↔ `flowchart TD`——链长就竖排，同层分支多就横排），[人工智能发展简史](../01-ai-basics/ai-history.md) 的 11 个节点拆成两行时间线并补了读图说明，[Claude Agent SDK](../18-frontier-2026/claude-agent-sdk.md) 的时序图把长消息用 `<br/>` 折行，[框架选型决策流](../09-frameworks/README.md) 精简了分流标签的措辞。节点内容与语义不变，只动排布与折行。
- **量出来的结果**：全库最宽块从 2664px 降到 1328px；被改的 17 块现在最小字号 ≥13.5px（多数恢复满尺寸 16px）。168 块真解析器仍 0 失败，无断链回归，frontmatter 逐文件校验通过。
- **留下的取舍如实写清楚**：还有 25 个块在 1128–1328px 之间（缩小后 13.5–15.9px，可读但不够舒展），没有为了凑指标继续砍节点；另外长链改竖排后图形变成「窄而高」（宽 256–400px、高约 1000px），左右留白偏多——这是拿版面换清晰度的主动选择，比文字糊成一片好。
- **规范固化**：[风格指南](../14-templates/style-guide.md) 新增「排布与可读性」小节与自检项——横向不超过 6 个节点，别指望用 `subgraph` 里的 `direction` 做泳道（一旦有边跨过子图边界，Mermaid 就忽略它），新图必须截**线上**页面判定。

## 2026-09-22（第 11 次）真实产品截图上线 + 无图页补齐 + 薄页增厚

全书第一次出现**真实软件界面**：此前 191 张配图全是自绘 SVG 与 Mermaid，读者看不到「这些工具真长什么样」。这一版补上截图，同时清掉三类体检出的短板。

- **8 张真实产品 UI 截图**（`docs/.gitbook/assets/screenshots/`，目录内 `MANIFEST.md` 逐张记录来源 URL 与访问日期）：Langfuse Trace 视图（11 章）、MCP Inspector 协议监控（05 章）、OpenHands Automate（12 章 + 项目页）、Dify 工作流画布（09 章）、Open WebUI 对话与工作区（12 章）、Arize Phoenix Trace Details（11 章）、AutoGen Studio Team Builder（09 章）、LangSmith 实验对比表（10 章）。每张逐项目检：真实产品界面、无 cookie 横幅与遮罩、文字可辨；7 个来源 URL 复核 HTTP 200。**每张图配一段「读这张图的顺序」**，指出面板与本页论点的对应关系，而不是贴完就算。
- **补齐违反「每页有图」自订标准的页面**：[Lab 2](../19-labs/lab2-rag.md) BM25 检索链路、[Lab 3](../19-labs/lab3-mcp.md) MCP 握手时序、[Lab 5](../19-labs/lab5-eval-trace.md) 评测—trace 数据流、[Lab 6](../19-labs/lab6-guardrails.md) 两道护栏决策流，各配一张章色 Mermaid；新图全部经 Edge 真实渲染逐张目检：Lab 3 用时序图，Lab 2/5/6 用竖排 `flowchart TD`。Lab 2 首版试过单排横向 LR，十个节点被正文宽度压到看不清字号，改回竖排后每张卡片文字都清晰，并把「回答不合格就回查切块与打分」这条虚线显式画了出来。
- **13 章 5 个薄项目页增厚**：[LangGraph](../13-resources/projects/langgraph.md)、[AutoGen](../13-resources/projects/autogen.md)、[CrewAI](../13-resources/projects/crewai.md)、[LangChain](../13-resources/projects/langchain.md)、[OpenHands](../13-resources/projects/openhands.md) 从 575–820 字扩到与其它资源页同密度（架构要点 + 适用场景 + 手写点评 + 真实链接），并把 7 个项目页全部配图；LangChain 页补 3 行 Runnable 管道代码判断协议价值。
- **核心页补最小可跑代码**：[Transformer 与注意力](../03-llm/transformer-attention.md) 新增 12 行 NumPy 单头因果注意力，与正文公式逐项对应，**贴出本机真实运行的权重矩阵输出**，并解释三件事：causal mask 就是「逐字解码」的代码形态、平方级开销长在权重矩阵上（所以 KV 缓存救显存救不了注意力）、softmax 饱和为什么让注意力可视化容易骗人。
- **未能做到的部分如实记录**：LangGraph Studio 与 browser-use 的官方文档页经渲染后 DOM 里只有品牌图，无公开产品截图；CrewAI 文档站的 `crews.png` / `flows.png` 目检是概念示意图（与自绘 Mermaid 等价），故不引入；Langfuse Cloud 官方 demo 工作区跳登录墙，改用其文档内嵌截图。原因写进 MANIFEST，避免后人重复踩。

统计更新：全书配图 **210 张**（168 Mermaid + 34 自绘 SVG + 8 真实截图），187 页 / 19 章不变；168 个 Mermaid 块经真解析器逐块校验 0 失败，无断链回归。提示卡重新逐文件点数：源码里的 hint 标记共 207 处，其中 4 处是 14 章模板代码块里的写法示例、1 处是本文的自指说明，都不会渲染成卡片，**真实提示卡 202 个**——此前两处统计分别写成 206 和 204，均以本次点数为准。

## 2026-09-21（第 10 次）动手实验章 + 门面升级 + 术语速查 + 实战手记

把「只读不练」和「门面朴素」两块最后的短板补齐，四件事一起落地：

- **新增第 19 章「动手实验」**：6 个纯标准库、零 API Key、离线可跑的实验——最小 ReAct 闭环 → 手写迷你 BM25 RAG → 手写迷你 MCP 服务 → 三角色协作 → 评测与 trace → 护栏与接真模型。每个实验含完整代码、**本机 Python 3.13 真实运行输出**、盯三个细节、动手改与排错备忘；MockLLM 与真实模型接口同构，看懂后换真 API 主循环一行不改。已接入 [SUMMARY](../SUMMARY.md) 与 [学习路线](../00-index/learning-path.md)（新增「动手派」路线）
- **门面升级**：自绘仓库封面 `cover-handbook.svg`（1600×900，六段学习旅程）+ GitBook 首页横幅 `banner-home.svg`（1920×480，LLM 推理循环）；[仓库首页](https://github.com/funny8kids/ai-agent-handbook)（在 GitHub 上，不在 GitBook 站内的 `docs/` 内容根里）与 [在线首页](../README.md) 重排，新增「边学边做」入口
- **4 张高保真工具界面示意**（与既有 SVG 同风格，逐张真实渲染目检）：MCP Inspector 调试台（05）、框架选型五问决策树（09）、Agent 评测发布门禁看板（10）、可观测性三跳定位控制台（11）
- **每章末尾中英术语速查**：核心章节各配 8–12 条术语 + 白话解释；**12 个核心页新增「实战手记」**：运维现场的经验值（轮次收敛区间、trace 采样账单、prompt 约束条数上限、检索失败要到日志认领等），数字全走经验口径、不虚构事故与引用

全书配图达 **191 张**（157 Mermaid + 34 自绘 SVG），提示卡 206 个；全部 Mermaid 经真解析器逐块校验 0 失败，无断链回归。

## 2026-09-20（第 9 次）旗舰概念插图第二批：8 张自绘 SVG 上线

补上「只有框图、没有图册」的最后一块短板，为核心概念页新增 8 张与既有资产同风格的自绘 SVG（960 宽、淡网格第二层背景、章色主色、语义化 SMIL 动效，全部经真实渲染逐张目检）：

| 插图 | 接入页面 | 讲什么 |
|---|---|---|
| 上下文预算 | [Token 与上下文](../03-llm/token-embedding-context.md) | 200k 窗口五段分配 + 压缩前后对照，缓存分界一眼可见 |
| ReAct 闭环 | [ReAct](../04-prompt-reasoning/react.md) | 思考—行动—观察三环，左侧纯 CoT 断链对照、右侧真实轨迹示例 |
| MCP 架构 | [MCP](../05-tool-protocol/mcp.md) | M×N 乱麻 vs M+N 统一协议，Host/Client/Server 与三种原语 |
| 记忆三层 | [记忆类型](../06-memory-rag/memory-types.md) | 工作/情景/语义的沉淀与回填回路 + 遗忘曲线 |
| 规划对比 | [Plan-and-Execute](../07-planning/plan-and-execute.md) | 先谋后动 vs 边想边做双泳道，含重规划回跳与两本账 |
| 协作拓扑 | [多智能体协作](../08-multi-agent/multi-agent-collaboration.md) | Supervisor/Swarm/Group Chat/Pipeline 四宫格与选型底线 |
| Trace 瀑布 | [日志、追踪与监控](../11-engineering/logging-tracing-monitoring.md) | 一次运行的 span 树时间轴，延迟/token/成本/重试四项必录 |
| 编程 Agent 循环 | [编程 Agent](../12-applications/coding-agent.md) | 沙箱内改码—测试—修复闭环，合并权留给人 |

全书配图达 **182 张**（154 Mermaid + 28 自绘 SVG）。

## 2026-09-20（第 8 次）全书 Mermaid 章色配色：告别默认灰白

针对线上抽查发现的「全书图只有黑白框图、图册感弱」做视觉体系升级：

- **154 个 Mermaid 块全部注入 `%%{init}%%` 章色主题**：18 章各配一个主色（02 紫、05 青、09 玫红、10 红……），节点底色统一为主色掺白 90%、连线掺白 45%，一眼可辨所在章节；GitHub 与 GitBook 原生支持该指令
- **门面页补图**：[什么是 AI Agent](../02-agent-basics/what-is-agent.md) 新增「两分钟判断是不是 Agent」决策流程图，全书正文页（除模板页）实现图零空白
- **规范固化**：[风格指南](../14-templates/style-guide.md) 新增「Mermaid 章色配色（硬性要求）」一节——章色表、混色公式、可直接复制的指令示例；写作检查清单同步加一条
- 全部 154 块经真解析器（mermaid@11）逐块校验 0 失败

## 2026-09-20（第 7 次）对标头部开源手册：图文、排版与自测体系升级

以 GitHub 同类头部项目（bojieli/ai-agent-book、microsoft/ai-agents-for-beginners、huggingface/agents-course、datawhalechina/self-llm 等）为参照，补三块短板：

- **图示密度翻倍**：新增约 60 张 Mermaid 内联图，全书达 **154 张 Mermaid + 20 张自绘 SVG**；09 框架、10 评安、11 工程、17 具身、16 基础设施等此前无图的章节全部配齐机制图；资源深读卡（ReAct/Reflexion/Toolformer/SWE-bench/GAIA/WebArena/Langfuse 等）逐张配「一图看懂」
- **排版升级为 GitBook 原生**：183 个「一句话 / 提示 / 注意」引用块全部转为分色 `{% hint %}` 提示卡；模板与风格指南同步改用 hint 写法，贡献指南新增「图文与排版规范」与 good-first-page 清单
- **每章「读完能做到」清单 + 章末自测**：18 章全量落地，清单条目均为可检验行为，自测题按回忆/应用/判断三档并标注答案出处
- **质量闸门**：全部 Mermaid 经真解析器（mermaid@11）逐块校验 0 失败；修复断链 5 处；被修改页面 `updated` 统一为 2026-09-20
- 资源库增补：开源项目索引头部 95 个项目改为手写一句话点评（去掉截断的机器味描述）；博客（16）/ 社区（11）/ Awesome 列表（13）/ 数据集四个索引扩充完成，收录链接逐一在线核验，无法核实的一律剔除

## 2026-09-12（第 6 次）对齐 2026-09 前沿：新增第 18 章

针对审核发现的「模型面/产品面/评估代际滞后、图片覆盖不足」做系统补强：

- **新增 18 2026 前沿**（8 页）：
  - [2026 前沿模型地图](../18-frontier-2026/frontier-models-2026.md)：GPT-6 Astra、Claude Fable 5.1 / Mythos 5.1、Opus 5，含 effort × 防护 × cache 读法
  - [OpenAI Agents API](../18-frontier-2026/openai-agents-api.md)：托管 Codex harness、压缩、tool search、子 Agent
  - [Claude Agent SDK](../18-frontier-2026/claude-agent-sdk.md)：与 CLI / Client SDK / Managed Agents 分界
  - [模型原生 vs 自建 Harness](../18-frontier-2026/model-native-vs-harness.md)：2026 架构分叉与选型流程
  - [Computer Use 2026](../18-frontier-2026/computer-use-2026.md)
  - [评估 2026](../18-frontier-2026/eval-2026.md)：Terminal-Bench 4.0、OSWorld 2.0、τ²、Agents' Last Exam
  - [2026 协议栈](../18-frontier-2026/protocol-stack-2026.md)：MCP + A2A + AG-UI + Skills/agents.md
- **第 10 章**新增 [2026 安全现实](../10-evaluation-safety/safety-incidents-2026.md)；[基准测试总览](../10-evaluation-safety/benchmarks.md) 刷新到 2026 代际
- **第 12 章**新增 [通用 Agent 产品](../12-applications/general-agent-products.md)、[实时语音 Agent](../12-applications/voice-agent.md)
- **第 01 章** [发展简史](../01-ai-basics/ai-history.md) 时间线补 2026-07～09 事件
- 新增 5 张自绘 SVG：模型×harness 矩阵、Agents API 架构、协议栈、评估版图、Computer Use 闸门
- 导航同步：`SUMMARY.md`、总导航、首页必读与主题入口

## 2026-09-10（第 5 次）内容质量修订与全书扩写

针对「模板化、emoji 泛滥、原理不深、引用单一」四类问题做系统性修订，并对全书 70 篇偏薄页面做深度扩写：

- 重写 [风格指南](../14-templates/style-guide.md)：按**体裁分型**（原理型/概念型/实战型/资源卡片），去掉单一模板；新增 emoji 硬预算、公式与出处要求、案例配给、发布字数门槛；并入 16/17 章的 SVG（SMIL）动图规范
- 全局清理 emoji：剥离标题 emoji 与星级难度标记；第 16/17 章 24 个文件一并去 emoji（627 → 163）
- 事实核查（经本地代理联网）：逐条验证外链；修复断链（`humanlayer/12-factor-agents`、`Awesome-RAG`、MCP Discussions 地址等）
- **Pi 仓库已迁移**：`badlogic/pi-mono` → `earendil-works/pi`，全库更新；移除已无法核实的「vLLM pods」等表述
- **DeepSeek Harness 引用经核实为真实**（包路径均存在），删除与主题弱相关的凑数引用
- 约 70 篇原理/概念/实战页补齐机制、公式与论文引用：注意力、Embedding、RLHF/DPO、预训练与 LoRA、量化推理、Token 与上下文预算、RAG 指标、CoT/ToT/GoT/Reflexion/Self-Refine、知识图谱、上下文工程、记忆压缩、幻觉、提示注入/越狱，规划 5 篇、多智能体 7 篇、框架 8 篇、工程化 10 篇、应用 8 篇，以及可解释性、对齐、行业 Agent 等
- **全书 170 页全部达到体裁字数门槛**（原理型 1200 / 实战型 900 / 概念型 600 汉字），含公式页面 93 篇
- 2 个不足 150 字的资源卡片补齐后恢复 `published`
- 新增 7 张自绘 SVG 插图并接入对应章节
- 新增 [开源项目索引](../13-resources/projects/README.md)：323 个项目、11 个分类，star/许可为 2026-09 实测值；后续清理了自动分类混入的跑题条目
- 说明：生成与校验用的辅助脚本已从仓库移除，以保持内容仓库精简

## 2026-09-10（第 4 次）新增 16 AI 基础设施与 17 具身智能

- 新增 **16 AI 基础设施**（11 页）：推理服务化（连续批处理 / PagedAttention / TTFT-TPOT）、前缀缓存与上下文工程、GPU 调度与多租户、训练与微调基础设施、沙箱与执行环境、模型网关与路由、持久化执行与运行时、数据与检索基础设施、可观测性与评估平台、推理经济学与部署形态
- 新增 **17 具身智能**（13 页）：具身闭环定义、机器人基础模型谱系（RT-2 → OpenVLA → π0 → GR00T/Helix/GO-1）、VLA 架构与动作头、动作表示与分层控制、数据引擎、仿真与 Sim-to-Real、世界模型与视频预训练、灵巧操作、人形与腿足运动、评估与基准、硬件实时与安全、Agent ⇄ 机器人桥接（含代码）
- 新增 6 张**可动画的 SVG 图示**（SMIL，GitHub/GitBook 中可直接播放）：连续批处理、前缀缓存、沙箱分层、VLA 循环、动作分块、Sim-to-Real 域随机化
- 双向链接补齐：16/17 ⇄ 03、05、06、10、11、12、13 各相关页；新增 `infrastructure`、`embodied-ai`、`data`、`cost` 四个标签
- 导航同步：`SUMMARY.md`、`docs/README.md`、学习路线（新增「平台/Infra」与「具身方向」两条路线）、术语表新增两组共 29 条

## 2026-09-10（第 3 次） 全书完成

- ✅ 全部 16 章、142 页撰写完成（此前为骨架 + 占位页）
- 案例覆盖三大开源 harness：**Claude Code**（社区逆向：三层 prompt 组装、子 Agent 隔离、三档压缩、权限管道）、**Pi Agent（原 pi-mono）**（极简 harness：4 原子工具、~300 行 agentLoop、JSONL 会话）、**DeepSeek Harness**（一切皆插件：Cordis 框架、turn/step 状态机、append-only 事件流、landlock 沙箱）
- 新增 12 章编程 Agent 页的「三大 harness 横向深拆」对比表
- 全书双向链接（知识点 ⇄ 资源）铺设完成；术语表 60+ 条收录
- 评估章收录五大基准精读（SWE-bench/GAIA/WebArena/AgentBench/ToolBench）

## 2026-09-10（第 2 次）

- 建立统一写作规范：新增 [风格指南](../14-templates/style-guide.md)（emoji 规范、图文规范、先问题后定义、写作检查清单）
- 知识点模板升级为「一句话结论 + 生活类比 + 图 + 例子 + 误区 + 资源」结构，增加 frontmatter（tags/type/status/updated）
- 资源模板增加 frontmatter 与「双向链接」规范（知识点 ⇄ 资源互链）
- 写出第一篇完整示例页：[什么是 AI Agent](../02-agent-basics/what-is-agent.md)
- 新增 `docs/assets/` 图片目录（diagrams / screenshots / covers / icons）
- SUMMARY 章节标题加入模块 emoji；全部占位页升级为新格式（frontmatter + 模块 emoji + 模板指引）

## 2026-09-10

- 初始化全新手册结构：16 个章节、135+ 页面骨架
- 建立导航与索引（总导航、学习路线、标签索引、资源总表、更新日志）
- 建立 13 资源库分类：论文、课程、开源项目、工具、数据集、基准测试、博客、社区、Awesome 列表
- 新增知识点模板与资源模板，统一写作格式
- 迁移 GitBook 配置，内容根目录设为 `docs/`
