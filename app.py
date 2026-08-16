"""
langchain_agent/app.py
Streamlit 界面：输入请假申请 → 看 LangChain Agent 自主调工具 → 看审批结论。
运行：streamlit run app.py  （默认 http://localhost:8503，避开项目1 的 8501 / 项目2 的 8502）
"""
import json
import streamlit as st

from agent import run

st.set_page_config(page_title="LangChain 请假审批 Agent", page_icon="🤖")
st.title("🤖 智能请假审批 Agent（LangChain 版）")
st.caption("与 leave_agent（原生版）做同一件事——用 LangChain 框架的 AgentExecutor 让模型自主多步调用工具")

with st.sidebar:
    st.markdown("### 这是什么")
    st.markdown(
        "本项目的 Agent 用 **LangChain** 框架实现：\n"
        "1. `search_leave_policy` 检索制度（RAG）\n"
        "2. `count_leave_days` 计算天数\n\n"
        "模型自己决定**调哪个、调几次**，最后输出结构化审批 JSON。\n\n"
        "对比 `leave_agent/`：那个是**原生**写死流水线 / Function Calling，"
        "这个是**框架**编排——同一需求两种实现，面试能讲清楚差异。"
    )

default_text = "我是张三，想请病假3天，从2026-08-17到2026-08-19，感冒发烧去医院看了，有病历。"
text = st.text_area("📝 粘贴一条请假申请", value=default_text, height=140)

if st.button("🚀 提交审批", type="primary"):
    if not text.strip():
        st.warning("请先输入请假申请。")
    else:
        with st.spinner("Agent 正在多步规划并调用工具…"):
            result = run(text)

        st.success("✅ Agent 处理完成")
        st.subheader("🛠️ Agent 自主调用的工具（Function Calling 轨迹）")
        trace = result.get("trace", [])
        if not trace:
            st.info("本次模型未调用工具（直接给出结论）。")
        for i, step in enumerate(trace, 1):
            with st.expander(f"第 {i} 步 · {step['name']}", expanded=True):
                st.write("**输入参数**：", step.get("args"))
                st.write("**工具返回**：")
                st.code(str(step.get("result"))[:1500])

        st.subheader("📋 审批结论")
        decision = result.get("decision")
        color = {"approve": "🟢", "request_info": "🟡", "reject": "🔴"}.get(decision, "⚪")
        label = {"approve": "批准", "request_info": "需补材料", "reject": "驳回"}.get(decision, decision)
        st.markdown(f"### {color} 结论：{label}")
        st.write("**理由：**")
        for r in result.get("reasons", []):
            st.markdown(f"- {r}")
        if result.get("missing"):
            st.write("**缺失材料：**")
            for m in result["missing"]:
                st.markdown(f"- {m}")

        with st.expander("查看原始返回 JSON"):
            st.json(result)
