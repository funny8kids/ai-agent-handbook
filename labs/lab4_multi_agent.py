# -*- coding: utf-8 -*-
"""Lab 4 三角色多智能体：Planner -> Executor -> Reviewer，带返工闭环。

多 Agent 系统最容易被讲玄。本实验把它压回三件事：
  1) 角色 = 同一个 MockLLM 换不同 system prompt
  2) 协作 = 一条共享的消息总线（list）
  3) 质量控制 = Reviewer 否决后，把意见回流给 Executor 重做（有重试上限）

运行：python lab4_multi_agent.py
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")  # 防 Windows 控制台 GBK 乱码

TASK = "给一本讲 AI Agent 的中文手册写一句首页标语，要求不超过 15 字"

class MessageBus:
    """共享上下文：所有角色的发言按序留痕——这就是多 Agent 的'群聊记录'。"""
    def __init__(self):
        self.log = []

    def post(self, role, text):
        self.log.append((role, text))
        print(f"  [{role:8s}] {text}")

    def last(self, role):
        for r, t in reversed(self.log):
            if r == role:
                return t
        return ""

def planner(bus):
    bus.post("planner", "拆两步：① Executor 产出 3 个候选标语；② Reviewer 按'≤15字+含动词'标准挑一个，不合格打回。")
    bus.post("planner", "验收标准：字数≤15、有动词、说清'给谁、有什么用'。")

def executor(bus):
    attempt = sum(1 for r, _ in bus.log if r == "reviewer")   # 被驳回次数
    if attempt == 0:
        bus.post("executor", "候选：A「让 Agent 从 demo 走向生产」 B「AI Agent 学习手册」 C「懂原理的 Agent 都省心」")
    else:
        feedback = bus.last("reviewer")
        bus.post("executor", f"（收到意见「{feedback[:18]}…」，修订）候选：D「手把手带你上线真 Agent」")

def reviewer(bus):
    text = bus.last("executor")
    cands = re.findall(r"「([^」]+)」", text)  # 标语里可能有空格，必须整体提取
    for c in cands:
        if len(c) <= 15 and any(v in c for v in ("走向", "上线", "带你")):
            bus.post("reviewer", f"通过：「{c}」（{len(c)} 字，含动词，说清价值）")
            return c
    bus.post("reviewer", "打回：没有同时满足 字数≤15 + 含动词 + 说清价值 的候选")
    return None

def run(max_rounds=3):
    print("=" * 62)
    print(f"Lab 4：三角色协作（任务：{TASK}）")
    print("=" * 62)
    bus = MessageBus()
    planner(bus)
    for rnd in range(1, max_rounds + 1):
        print(f"\n--- 第 {rnd} 轮 ---")
        executor(bus)
        pick = reviewer(bus)
        if pick:
            bus.post("planner", f"任务完成，采用「{pick}」。共 {rnd} 轮，消息数 {len(bus.log) + 1}")
            return pick
    bus.post("planner", "到达最大轮数，升级给人（真实系统必须有的兜底）")
    return None

if __name__ == "__main__":
    result = run()
    print("\n最终标语:", result or "（无，需人工介入）")
    print("要点：所谓'多智能体框架'，剥开外壳就是 角色提示词 + 消息总线 + 重试/升级策略。")
