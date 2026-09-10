#!/usr/bin/env python3
"""从 .tmp-projects/cache.json 生成 docs/13-resources/projects/README.md。

数据来源：GitHub Search + Repos API（经本地代理抓取），star 数为 2026-09 观测值。
重新生成：python scripts/gen-projects.py
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, '.tmp-projects', 'cache.json')
OUT = os.path.join(ROOT, 'docs', '13-resources', 'projects', 'README.md')
DATE = '2026-09'

CATS = [
    ('Agent 框架与编排', ['agent framework', 'agentic framework', 'llm framework', 'orchestration',
        'workflow engine', 'langgraph', 'autogen', 'crewai', 'dspy', 'agents sdk', 'agent development',
        'llmops', 'prompt framework', 'agentic', 'workflow automation', 'low-code', 'pipeline']),
    ('编程 Agent 与 Harness', ['coding agent', 'code agent', 'software engineering agent', 'swe',
        'autonomous coding', 'code generation', 'pair programming', 'codex', 'claude code', 'aider',
        'openhands', 'gpt-pilot', 'swe-agent', 'code assistant', 'ide', 'developer tool', 'copilot',
        'terminal agent', 'cli agent']),
    ('多智能体', ['multi-agent', 'multiagent', 'multi agent', 'swarm', 'agent collaboration',
        'agent society', 'agent team', 'group chat', 'meta-gpt', 'metagpt', 'agent framework for teams']),
    ('记忆与 RAG', ['rag', 'retrieval augmented', 'retrieval-augmented', 'vector database', 'vector store',
        'vector search', 'embedding', 'knowledge graph', 'graphrag', 'agent memory', 'semantic search',
        'rerank', 'chunking', 'document qa', 'knowledge base', 'similarity search']),
    ('工具与协议', ['mcp', 'model context protocol', 'tool calling', 'function calling', 'a2a',
        'agent protocol', 'agent tool', 'llm tool', 'toolkit for', 'agent-to-agent',
        'agents sdk', 'tool integration', 'composio']),
    ('浏览器与 Computer Use', ['browser automation', 'browser agent', 'computer use', 'gui agent',
        'web agent', 'web automation', 'playwright', 'selenium', 'desktop automation', 'vision agent',
        'headless browser', 'scraping agent']),
    ('可观测、评估与安全', ['observability', 'tracing', 'evaluation', 'llm eval', 'monitoring',
        'prompt testing', 'guardrails', 'llm judge', 'hallucination', 'red team', 'jailbreak',
        'prompt injection', 'safety', 'security', 'governance', 'metrics']),
    ('推理与部署', ['inference', 'serving', 'llm serving', 'quantization', 'gguf', 'vllm', 'ollama',
        'llama.cpp', 'deployment', 'llm runtime', 'tensorrt', 'onnx', 'gpu', 'model compression',
        'distillation', 'finetuning', 'fine-tuning', 'training']),
    ('沙箱与运行时', ['sandbox', 'code execution', 'code interpreter', 'microvm', 'container',
        'runtime for agents', 'e2b', 'firecracker', 'isolated execution', 'untrusted code']),
    ('基准、数据集与论文', ['benchmark', 'dataset', 'leaderboard', 'evaluation suite', 'test suite',
        'arena', 'paper', 'research', 'survey']),
    ('学习资源与 Awesome', ['awesome', 'tutorial', 'course', 'book', 'handbook', 'guide', 'roadmap',
        'learning', 'examples', 'cookbook', 'curated list', 'beginners', '笔记']),
]

# 必须收录（修正自动分类），key 为小写 full_name，value=(分类, 说明覆盖)
SEED = {
    'langchain-ai/langchain': 'Agent 框架与编排', 'langchain-ai/langgraph': 'Agent 框架与编排',
    'microsoft/autogen': '多智能体', 'microsoft/agent-framework': 'Agent 框架与编排',
    'crewaiinc/crewai': '多智能体', 'stanfordnlp/dspy': 'Agent 框架与编排',
    'run-llama/llama_index': '记忆与 RAG', 'microsoft/semantic-kernel': 'Agent 框架与编排',
    'openai/openai-agents-python': 'Agent 框架与编排', 'openai/swarm': '多智能体',
    'huggingface/smolagents': 'Agent 框架与编排', 'letta-ai/letta': '记忆与 RAG',
    'geekan/metagpt': '多智能体', 'significant-gravitas/autogpt': 'Agent 框架与编排',
    'yoheinakajima/babyagi': 'Agent 框架与编排', 'n8n-io/n8n': 'Agent 框架与编排',
    'all-hands-ai/openhands': '编程 Agent 与 Harness', 'swe-agent/swe-agent': '编程 Agent 与 Harness',
    'aider-ai/aider': '编程 Agent 与 Harness', 'openai/codex': '编程 Agent 与 Harness',
    'google-gemini/gemini-cli': '编程 Agent 与 Harness', 'block/goose': '编程 Agent 与 Harness',
    'deepseek-ai/deepseek-harness': '编程 Agent 与 Harness', 'earendil-works/pi': '编程 Agent 与 Harness',
    'pythagora-io/gpt-pilot': '编程 Agent 与 Harness', 'princeton-nlp/swe-agent': '编程 Agent 与 Harness',
    'browser-use/browser-use': '浏览器与 Computer Use', 'microsoft/playwright-mcp': '浏览器与 Computer Use',
    'modelcontextprotocol/servers': '工具与协议', 'modelcontextprotocol/modelcontextprotocol': '工具与协议',
    'google/a2a': '工具与协议', 'google/adk-python': '工具与协议',
    'mem0ai/mem0': '记忆与 RAG', 'microsoft/graphrag': '记忆与 RAG', 'hkuds/lightrag': '记忆与 RAG',
    'neo4j-labs/llm-graph-builder': '记忆与 RAG', 'qdrant/qdrant': '记忆与 RAG',
    'milvus-io/milvus': '记忆与 RAG', 'weaviate/weaviate': '记忆与 RAG',
    'chroma-core/chroma': '记忆与 RAG', 'pgvector/pgvector': '记忆与 RAG',
    'facebookresearch/faiss': '记忆与 RAG', 'langgenius/dify': '记忆与 RAG',
    'langfuse/langfuse': '可观测、评估与安全', 'arize-ai/phoenix': '可观测、评估与安全',
    'explodinggradients/ragas': '可观测、评估与安全', 'promptfoo/promptfoo': '可观测、评估与安全',
    'berriai/litellm': '推理与部署', 'vllm-project/vllm': '推理与部署', 'ollama/ollama': '推理与部署',
    'ggml-org/llama.cpp': '推理与部署', 'huggingface/trl': '推理与部署',
    'e2b-dev/e2b': '沙箱与运行时', 'firecracker-microvm/firecracker': '沙箱与运行时',
    'princeton-nlp/swe-bench': '基准、数据集与论文', 'thudm/agentbench': '基准、数据集与论文',
    'sierra-research/tau-bench': '基准、数据集与论文', 'openbmb/toolbench': '基准、数据集与论文',
    'e2b-dev/awesome-ai-agents': '学习资源与 Awesome', 'kyrolabs/awesome-agents': '学习资源与 Awesome',
    'punkpeye/awesome-mcp-servers': '学习资源与 Awesome', 'microsoft/ai-agents-for-beginners': '学习资源与 Awesome',
    'humanlayer/12-factor-agents': '学习资源与 Awesome',
}

MIN_STARS = 400
PER_CAT = 34
# 明确跑题或质量不匹配的条目：人工拉黑，避免污染索引
BLOCK = {
    'naalytics/assemblies-of-putative-sars-cov2-spike-encoding-mrna-sequences-for-vaccines-bnt-162b2-and-mrna-1273',
    'mikeroyal/self-hosting-guide', 'accumulatemore/cv', 'open-metadata/openmetadata',
    'standardagents/arrow-js', 'th0rgal/sandboxed.sh', 'nextlevelbuilder/goclaw',
    'jo-inc/camofox-browser', 'h4ckf0r0day/obscura', 'lexmount/moli',
    'ifixai-ai/ifixai', 'raga-ai-hub/ragaai-catalyst', 'karpathy/autoresearch',
}
# 必须命中「Agent 相关」强信号，避免只靠泛 AI 词混进来
STRONG = ['agent', 'llm', 'rag', 'mcp', 'prompt', 'langchain', 'langgraph', 'gpt',
          'embedding', 'vector', 'retrieval', 'fine-tun', 'transformer', 'llmops',
          'multi-agent', 'tool call', 'tool-call', 'hallucination', '智能体']
# 全局相关性闸门：必须命中其一，避免把泛 AI 项目混进来
GATE = ['ai', 'llm', 'agent', 'gpt', 'model', 'rag', 'mcp', 'prompt', 'neural',
        'transformer', 'embedding', 'machine learning', 'deep learning', 'genai', 'copilot']
# 负向词：命中则排除（与 Agent 工程无关的领域）
NEG = ['service discovery', 'quant investment', 'video production', 'game engine',
       'e-commerce', 'ecommerce', 'blockchain', 'crypto', 'cms', 'blog theme',
       'product analytics', 'web analytics', 'note-taking', 'portfolio', 'dating']

# 仓库里已有的深入卡片页（保持双向导航）
CARDS = [
    ('LangChain', 'langchain.md'), ('LangGraph', 'langgraph.md'),
    ('AutoGen', 'autogen.md'), ('CrewAI', 'crewai.md'), ('OpenHands', 'openhands.md'),
    ('DeepSeek Harness', 'deepseek-harness.md'), ('Pi Agent', 'pi.md'),
]


def passes_gate(v):
    hay = (v.get('full_name', '') + ' ' + (v.get('description') or '') + ' ' + topics_of(v)).lower()
    return any(g in hay for g in GATE)


def topics_of(v):
    t = v.get('topics') or []
    return ' '.join(t) if isinstance(t, list) else ''


def score(v, kws):
    hay = (v.get('full_name', '') + ' ' + (v.get('description') or '') + ' ' + topics_of(v)).lower()
    return sum(1 for k in kws if k in hay)


def fmt_stars(n):
    if n is None:
        return '—'
    if n >= 10000:
        return f'{n/10000:.1f} 万'
    return f'{n:,}'


def fmt_lic(v):
    lic = v.get('license') or ''
    lic = str(lic).replace(' License', '').strip()
    return lic or '—'


def main():
    cache = json.load(open(CACHE, encoding='utf-8'))
    low = {k.lower(): (k, v) for k, v in cache.items()}
    used = set()
    buckets = {name: [] for name, _ in CATS}

    # 1) 种子
    for key, cat in SEED.items():
        if key in low:
            real, v = low[key]
            if v.get('archived'):
                continue
            buckets[cat].append(v)
            used.add(real.lower())

    # 2) 自动分类填充
    for real, v in cache.items():
        if real.lower() in used or v.get('archived') or real.lower() in BLOCK:
            continue
        stars = v.get('stars') or 0
        if stars < MIN_STARS or not passes_gate(v):
            continue
        blob = (v.get('full_name', '') + ' ' + (v.get('description') or '') + ' ' + topics_of(v)).lower()
        if any(n in blob for n in NEG):
            continue
        if not any(s in blob for s in STRONG):   # 必须命中 Agent 强信号
            continue
        best, bs = None, 0
        for name, kws in CATS:
            s = score(v, kws)
            if s > bs:
                best, bs = name, s
        if best and bs >= 2:
            buckets[best].append(v)
            used.add(real.lower())

    # 3) 排序输出
    shown = {name: sorted(buckets[name], key=lambda v: (v.get('stars') or 0), reverse=True)[:PER_CAT]
             for name, _ in CATS}
    total = sum(len(v) for v in shown.values())

    lines = []
    lines.append('---')
    lines.append('tags: [resource, project]')
    lines.append('type: index')
    lines.append('status: published')
    lines.append(f'updated: 2026-09-10')
    lines.append('---')
    lines.append('')
    lines.append('# 开源项目索引')
    lines.append('')
    lines.append(f'> **一句话**：AI Agent 相关开源项目总览，按 11 类整理，收录 {total} 个；'
                 f'star 数与许可为 **{DATE}** 观测值。')
    lines.append('')
    lines.append('> **提示**：star 数只反映关注度，不反映质量与适配度；选型请结合活跃度与你的场景实测。'
                 '数据由 `scripts/gen-projects.py` 从 GitHub API 生成，可重新运行更新。')
    lines.append('')
    lines.append('## 深入卡片')
    lines.append('')
    lines.append('下面几个项目在本手册中有单独的深读卡片：')
    lines.append('')
    lines.append(' · '.join(f'[{n}]({p})' for n, p in CARDS))
    lines.append('')
    for name, _ in CATS:
        items = shown[name]
        if not items:
            continue
        lines.append(f'## {name}')
        lines.append('')
        lines.append('| 项目 | Star(%s) | 许可 | 语言 | 说明 |' % DATE)
        lines.append('|---|---|---|---|---|')
        for v in items:
            fn = v.get('full_name')
            desc = (v.get('description') or '').replace('|', '/').strip()
            if len(desc) > 110:
                desc = desc[:108] + '…'
            lines.append(f"| [{fn}]({v.get('html_url')}) | {fmt_stars(v.get('stars'))} | {fmt_lic(v)} | {v.get('language') or '—'} | {desc} |")
        lines.append('')
    lines.append('## 相关知识点')
    lines.append('')
    lines.append('- [框架与生态](../../09-frameworks/README.md)')
    lines.append('- [工具调用与协议](../../05-tool-protocol/README.md)')
    lines.append('- [记忆与 RAG](../../06-memory-rag/README.md)')
    lines.append('')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    print('written', OUT, 'total shown:', total)
    for name, _ in CATS:
        print(f'  {name}: {len(shown[name])}')


if __name__ == '__main__':
    main()
