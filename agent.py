"""
langchain_agent/agent.py

用 LangChain 框架实现「智能请假审批 Agent」——对比 leave_agent（原生实现）。
核心：AgentExecutor 让大模型自主多步规划、调用工具：
  - search_leave_policy(query)  检索公司请假制度（Chroma 向量库 RAG）
  - count_leave_days(start,end) 计算请假天数
模型自己决定调哪个工具、调几次，最后输出结构化审批结论 JSON。

运行依赖（已写入 requirements.txt）：
  langchain / langchain-openai / langchain-community / chromadb / openai / python-dotenv
"""
import os
import re
import json
from datetime import date

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

CHROMA_DIR = "chroma_lc_db"
DOC_PATH = "sample_docs/示例-公司请假制度.txt"

# ---------------------------------------------------------------------------
# 1) 大模型（DeepSeek，OpenAI 兼容）
# ---------------------------------------------------------------------------
_llm = ChatOpenAI(
    model=MODEL,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0,
)

# ---------------------------------------------------------------------------
# 2) 本地向量库（Chroma + 默认 embedding，复用项目1/2 的检索能力）
# ---------------------------------------------------------------------------
_client = chromadb.PersistentClient(path=CHROMA_DIR)
_ef = embedding_functions.DefaultEmbeddingFunction()
_coll = _client.get_or_create_collection("leave_policy_lc", embedding_function=_ef)


def _ensure_ingested() -> None:
    """首次调用时把制度文档切分入库；之后直接复用。"""
    if _coll.count() > 0:
        return
    if not os.path.exists(DOC_PATH):
        return
    with open(DOC_PATH, encoding="utf-8") as f:
        text = f.read()
    # 按空行分段，长段再按句号切，控制在 ~200 字内
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, buf = [], ""
    for p in paras:
        if len(buf) + len(p) < 200:
            buf += p
        else:
            if buf:
                chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    chunks = [c for c in chunks if c.strip()]
    if not chunks:
        return
    _coll.add(
        ids=[f"c{i}" for i in range(len(chunks))],
        documents=chunks,
    )


# ---------------------------------------------------------------------------
# 3) 工具定义（LangChain @tool 装饰器）
# ---------------------------------------------------------------------------
@tool
def search_leave_policy(query: str) -> str:
    """检索公司请假制度，返回与查询相关的条款文本。
    当需要根据制度判断请假是否合规、或想确认某种假期的材料/天数要求时使用。"""
    _ensure_ingested()
    res = _coll.query(query_texts=[query], n_results=3)
    docs = res.get("documents", [[]])[0]
    if not docs:
        return "未找到相关制度条款。"
    return "\n---\n".join(docs)


@tool
def count_leave_days(start_date: str, end_date: str) -> str:
    """计算请假天数（含首尾两天）。参数格式均为 YYYY-MM-DD。"""
    try:
        s = date.fromisoformat(start_date)
        e = date.fromisoformat(end_date)
    except ValueError:
        return "日期格式错误，应为 YYYY-MM-DD。"
    if e < s:
        return "结束日期早于开始日期。"
    days = (e - s).days + 1
    return f"从 {start_date} 到 {end_date} 共 {days} 天（含首尾）。"


# ---------------------------------------------------------------------------
# 4) Agent：用 LangChain 新版 create_agent（工具循环 + 结构化输出）
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """你是一个公司请假审批 Agent。
收到员工的请假申请后，按如下方式工作：
1. 必要时调用 search_leave_policy 检索相关制度条款；
2. 必要时调用 count_leave_days 计算请假天数；
3. 综合「申请内容 + 制度条款」给出审批结论。

审批结论的 decision 取值只能是：approve（批准）/ request_info（需补材料）/ reject（驳回）。
当 decision=request_info 时，missing 填写缺失的材料；否则 missing 为空列表。"""

# 结构化输出 schema（create_agent 的 response_format 会强制模型按此返回）
class LeaveDecision(BaseModel):
    decision: str = Field(description="审批结论：approve / request_info / reject")
    reasons: list[str] = Field(description="给出该结论的理由列表")
    missing: list[str] = Field(description="缺失的材料列表，无则空列表 []")


TOOLS = [search_leave_policy, count_leave_days]
_AGENT = create_agent(
    model=_llm,
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
    response_format=LeaveDecision,
)


def run(application_text: str) -> dict:
    """执行 Agent，返回 {decision, reasons, missing, trace}。"""
    result = _AGENT.invoke({"messages": [("user", application_text)]})

    # 结构化结论
    sr = result.get("structured_response")
    if isinstance(sr, LeaveDecision):
        data = sr.model_dump()
    elif isinstance(sr, dict):
        data = sr
    else:
        data = {"decision": "request_info", "reasons": ["模型未返回结构化结论"], "missing": []}
    data.setdefault("decision", "request_info")
    data.setdefault("reasons", [])
    data.setdefault("missing", [])

    # 提取工具调用轨迹（从消息列表里捞 tool_calls / ToolMessage）
    trace = []
    for m in result.get("messages", []):
        tcs = getattr(m, "tool_calls", None)
        if tcs:
            for tc in tcs:
                trace.append({"name": tc["name"], "args": tc["args"], "result": None})
        elif m.__class__.__name__ == "ToolMessage":
            # 把工具返回结果接到最近一个同名工具调用上
            for step in reversed(trace):
                if step["name"] == m.name and step["result"] is None:
                    step["result"] = m.content
                    break
    # 只保留真实业务工具，过滤掉 response_format 的结构化输出伪步骤
    real_tools = {t.name for t in TOOLS}
    data["trace"] = [t for t in trace if t["name"] in real_tools]
    return data


if __name__ == "__main__":
    sample = "我是张三，想请病假3天，从2026-08-17到2026-08-19，感冒发烧去医院看了，有病历。"
    res = run(sample)
    print(json.dumps(res, ensure_ascii=False, indent=2))
