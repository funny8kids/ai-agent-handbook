# -*- coding: utf-8 -*-
"""Lab 1 最小 ReAct 闭环：Thought -> Action -> Observation，直到 Final Answer。

零依赖，纯标准库，无需 API key：LLM 由一个"脚本化 MockLLM"扮演，
它根据当前轨迹（trajectory）决定下一步说什么——和真模型的行为接口完全一致，
换成真实模型只需替换 MockLLM 类（见 lab6 与页面说明）。

运行：python lab1_react.py
"""
import ast
import operator
import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台默认 GBK，中文输出会乱码

# ---------- 工具层：Agent 的"手" ----------

def calculator(expr: str) -> str:
    """安全四则运算：只允许数字与 + - * / ( )，不用 eval 裸跑。"""
    allowed = {ast.BinOp, ast.UnaryOp, ast.Expression, ast.Constant, ast.Load}
    ops = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv,
           ast.USub: operator.neg}

    def _ev(node):
        if type(node) not in allowed:
            raise ValueError(f"非法表达式: {expr}")
        if isinstance(node, ast.Expression):
            return _ev(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.UnaryOp):
            return ops[type(node.op)](_ev(node.operand))
        return ops[type(node.op)](_ev(node.left), _ev(node.right))

    return str(_ev(ast.parse(expr, mode="eval")))


DOCS = {
    "财报-甲公司": "甲公司 2025 年营收 4800 万元，同比增长 12%。",
    "财报-乙公司": "乙公司 2025 年营收 0.62 亿元，同比增长 5%。",
    "汇率": "2025 年参考汇率：1 美元 ≈ 7.2 元人民币。",
}

def search(query: str) -> str:
    """玩具搜索：按关键词命中返回文档，否则返回未找到。"""
    hits = [doc for key, doc in DOCS.items() if any(w in key for w in query.split())]
    return "\n".join(hits) if hits else "未找到相关结果"


TOOLS = {"calculator": calculator, "search": search}

# ---------- LLM 层：Agent 的"脑" ----------

class MockLLM:
    """脚本化模型：读入完整 prompt（含历史轨迹），输出下一段文本。

    输出协议与 ReAct 论文一致：
      Thought: ...
      Action: 工具名(参数)
    或
      Thought: ...
      Final Answer: ...
    """

    def __init__(self):
        self.step = 0

    def __call__(self, prompt: str) -> str:
        q = prompt.split("Question:", 1)[1].split("Thought:", 1)[0].strip()
        seen = prompt
        if "Action: search" not in seen:
            return f"Thought: 要比较两家公司营收，先查甲公司的财报。\nAction: search(财报-甲公司)"
        if "Action: calculator" not in seen:
            if "0.62" not in seen:
                return f"Thought: 甲公司数据已到手，再查乙公司。\nAction: search(财报-乙公司)"
            return ("Thought: 甲公司 4800 万元，乙公司 0.62 亿元=6200 万元，"
                    "用计算器换算确认。\nAction: calculator(0.62*10000)")
        return ("Thought: 6200 万元 > 4800 万元，乙公司营收更高。\n"
                f"Final Answer: 乙公司营收更高（约 6200 万元 vs 4800 万元），问题「{q}」已解决。")

# ---------- Agent 循环：本书反复出现的那个 while ----------

def run_agent(question: str, llm, max_steps: int = 6) -> str:
    prompt = f"Question: {question}\n"
    for i in range(1, max_steps + 1):
        out = llm(prompt)                       # 1. 模型基于全部历史生成下一步
        prompt += out + "\n"
        print(f"\n[step {i}] {out}")
        if "Final Answer:" in out:              # 2. 终止条件一：模型自己宣布完成
            return out.split("Final Answer:", 1)[1].strip()
        if "Action:" in out:                    # 3. 终止条件二之前，永远先执行工具
            call = out.split("Action:", 1)[1].strip()
            name, args = call.split("(", 1)
            args = args.rstrip(")")
            try:
                obs = TOOLS[name.strip()](args)
            except Exception as e:              # 工具报错也要回流，不能炸循环
                obs = f"工具错误: {e}"
            prompt += f"Observation: {obs}\n"
            print(f"          -> Observation: {obs}")
    return "到达 MAX_STEPS 兜底退出（防止一直转圈）"


if __name__ == "__main__":
    print("=" * 62)
    print("Lab 1：最小 ReAct 闭环（甲公司 vs 乙公司谁营收更高？）")
    print("=" * 62)
    answer = run_agent("甲公司和乙公司谁的 2025 年营收更高？", MockLLM())
    print("\n最终答案:", answer)
