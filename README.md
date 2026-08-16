# 智能请假审批 Agent · LangChain 版（简历项目 3）

用 **LangChain 框架**实现的「多步骤 Agent」：收到自然语言请假申请后，模型**自主规划**并调用工具——
检索公司制度（RAG）+ 计算请假天数——最后输出结构化审批结论。

> 这是简历项目 3，刻意与 [`leave_agent`](../leave_agent/)（**原生**实现）做**同一件事**：
> 一个需求、两种实现。面试官最爱问"框架和原生有什么区别"，你两张牌都能打。

## ✨ 框架版 vs 原生版 对比

| 维度 | leave_agent（原生） | 本项目（LangChain） |
|---|---|---|
| 编排方式 | 自己写 `while` 循环跑 Function Calling | `AgentExecutor` 框架托管循环 |
| 工具定义 | 手写 `TOOLS` JSON schema | `@tool` 装饰器 + 类型注解自动生成 schema |
| 多步决策 | 代码/模型混合控制 | 模型完全自主决定调哪个、调几次 |
| 中间过程 | 自己记录 `trace` | `return_intermediate_steps` 直接拿 |

## 🧱 技术栈

- **LangChain**：`create_tool_calling_agent` + `AgentExecutor`（多步 Agent 编排）
- **大模型**：DeepSeek（OpenAI 兼容，`ChatOpenAI` 接入）
- **工具**：`search_leave_policy`（Chroma 向量检索 RAG）、`count_leave_days`（日期计算）
- **结构化输出**：系统提示强制 JSON（`decision / reasons / missing`）
- **界面**：Streamlit（端口 8503）
- **语言**：Python 3.13

## 📁 项目结构

```
langchain_agent/
├── agent.py            # 核心：LangChain Agent（工具 + 执行器 + 解析）
├── app.py              # Streamlit 界面（输入申请 / 看工具轨迹 / 看结论）
├── test_agent.py       # 端到端验证（3 用例）
├── requirements.txt
├── .env.example        # 密钥模板（复制为 .env 后填 Key）
├── .gitignore
└── sample_docs/
    └── 示例-公司请假制度.txt
```

## 🚀 本地运行

```bash
cd langchain_agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # 填入你的 DEEPSEEK_API_KEY
streamlit run app.py        # 打开 http://localhost:8503
```

首次运行会自动用 Chroma 默认 embedding 把制度文档入库（本地，无需 Key）。

## 🔍 核心流程

```
申请文本
  │
  ▼
LangChain AgentExecutor（模型自主循环）
  ├─🔧 search_leave_policy(query)   → 检索相关制度条款（RAG）
  ├─🔧 count_leave_days(start,end)  → 计算请假天数
  │       ↑ 调哪个 / 调几次 由模型自己决定
  ▼
结构化审批 JSON：{ decision, reasons, missing }
```

## 💡 简历亮点

- 用 **LangChain 框架**落地多步骤 Agent（工具调用 + 自主规划）
- 同一需求对比**原生实现**与**框架实现**，体现"知其然也知其所以然"
- 融合 **RAG 检索 + 结构化 JSON 输出 + 合规推理**
- 可视化 Agent 决策过程（工具调用轨迹）

## 🔧 后续可扩展

- 接入 LangGraph 做带状态的复杂工作流
- 多轮追问补全缺失材料
- 接入真实 HR 系统自动发审批结果
