# -*- coding: utf-8 -*-
"""Lab 3 手写一个迷你 MCP：同一个文件扮演 server 与 client 两个进程。

MCP 的本质是「一条 stdin/stdout 上的 JSON-RPC 2.0 管道 + 三个约定方法」：
  initialize -> tools/list -> tools/call
本实验不用任何 SDK：client 用 subprocess 真的把 server 拉起来，
两边打印每一条原始报文——拆掉封装后你会发现协议薄得惊人。

运行：python lab3_mcp.py          （client 模式，会自动拉起自己当 server）
      python lab3_mcp.py serve    （server 模式，等 stdin 报文，一般不用手动跑）
"""
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")  # 防 Windows 控制台 GBK 乱码
sys.stdin.reconfigure(encoding="utf-8")   # server 侧必须按 UTF-8 解报文：否则中文按 GBK 拆成别的字，字数统计当场失真

# ---------- 共享：工具定义（server 的"能力清单"） ----------

TOOLS_SPEC = [
    {"name": "get_time",
     "description": "返回一个固定的演示时间戳（真实实现里这里查系统时钟）",
     "inputSchema": {"type": "object", "properties": {}, "required": []}},
    {"name": "word_count",
     "description": "统计一段文本的中英文字数",
     "inputSchema": {"type": "object",
                     "properties": {"text": {"type": "string", "description": "待统计文本"}},
                     "required": ["text"]}},
]

def tool_word_count(text: str) -> str:
    zh = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    en = len([w for w in "".join(c if c.isalnum() else " " for c in text).split()
              if any(ch.isascii() and ch.isalnum() for ch in w)])
    return json.dumps({"中文": zh, "英文单词": en}, ensure_ascii=False)

# ---------- Server 模式：读一行、回一行 ----------

def serve():
    """标准 I/O 上的 JSON-RPC 2.0 服务循环——这就是一个 MCP server 的全部骨架。"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        method, mid = msg.get("method"), msg.get("id")

        if method == "initialize":
            resp = {"jsonrpc": "2.0", "id": mid,
                    "result": {"protocolVersion": "2024-11-05",
                               "serverInfo": {"name": "lab3-mini-mcp", "version": "0.1.0"},
                               "capabilities": {"tools": {}}}}
        elif method == "notifications/initialized":
            continue                                   # 通知没有 id，不需要回复
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS_SPEC}}
        elif method == "tools/call":
            name = msg["params"]["name"]
            args = msg["params"].get("arguments", {})
            if name == "get_time":
                content = "2026-09-21T18:00:00+08:00（演示固定值）"
            elif name == "word_count":
                content = tool_word_count(args.get("text", ""))
            else:
                content = f"Error: 未知工具 {name}"
            resp = {"jsonrpc": "2.0", "id": mid,
                    "result": {"content": [{"type": "text", "text": content}],
                               "isError": name not in ("get_time", "word_count")}}
        else:
            resp = {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()

# ---------- Client 模式：拉起 server，走一遍完整会话 ----------

class MCPClient:
    def __init__(self):
        self.proc = subprocess.Popen(
            [sys.executable, __file__, "serve"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1)
        self.next_id = 0

    def _send(self, obj: dict, expect_reply=True):
        print(f"\n  >>> 发送: {json.dumps(obj, ensure_ascii=False)}")
        self.proc.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()
        if expect_reply:
            reply = json.loads(self.proc.stdout.readline())
            print(f"  <<< 收到: {json.dumps(reply, ensure_ascii=False)}")
            return reply

    def request(self, method, params=None):
        self.next_id += 1
        msg = {"jsonrpc": "2.0", "id": self.next_id, "method": method}
        if params:
            msg["params"] = params
        return self._send(msg)["result"]

    def notify(self, method):
        self._send({"jsonrpc": "2.0", "method": method}, expect_reply=False)

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=5)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        serve()
        sys.exit(0)

    print("=" * 62)
    print("Lab 3：手写迷你 MCP —— 两个真实进程之间的 JSON-RPC 对话")
    print("=" * 62)
    c = MCPClient()
    try:
        info = c.request("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "lab3-client", "version": "0.1.0"},
            "capabilities": {}})
        print(f"\n[握手完成] server={info['serverInfo']['name']} "
              f"protocol={info['protocolVersion']}")
        c.notify("notifications/initialized")

        tools = c.request("tools/list")["tools"]
        print(f"\n[能力发现] 共 {len(tools)} 个工具: "
              + ", ".join(t["name"] for t in tools))

        r1 = c.request("tools/call", {"name": "get_time", "arguments": {}})
        print(f"\n[调用 get_time]   -> {r1['content'][0]['text']}")

        r2 = c.request("tools/call", {"name": "word_count",
                                      "arguments": {"text": "MCP 让一个协议服务 N 个工具"}})
        print(f"[调用 word_count]  -> {r2['content'][0]['text']}")

        r3 = c.request("tools/call", {"name": "delete_all", "arguments": {}})
        print(f"[调用未知工具]     -> isError={r3['isError']} "
              f"{r3['content'][0]['text']}（协议不炸，错误也是数据）")
    finally:
        c.close()
    print("\n结论：MCP = 进程隔离 + JSON-RPC 三件套；SDK 只是把这层管道包起来。")
