"""
test_agent.py — 端到端验证 LangChain 请假审批 Agent（3 个用例）
运行：.venv/Scripts/python.exe test_agent.py
"""
from agent import run

CASES = [
    {
        "name": "病假3天 + 病历证明",
        "text": "我是张三，想请病假3天，从2026-08-17到2026-08-19，感冒发烧去医院看了，有病历。",
        "expect": "approve",
    },
    {
        "name": "病假2天 + 无证明",
        "text": "我是李四，想请病假2天，从2026-08-20到2026-08-21，身体不舒服。",
        "expect": "request_info",
    },
    {
        "name": "事假1天",
        "text": "我是王五，想请事假1天，2026-08-25，家里有事要处理。",
        "expect": "approve",
    },
]


def main():
    ok = 0
    for i, case in enumerate(CASES, 1):
        print(f"\n=== 用例 {i}: {case['name']} ===")
        res = run(case["text"])
        decision = res.get("decision")
        print(f"  决策={decision} | 期望={case['expect']} | 工具调用={len(res.get('trace', []))} 次")
        for r in res.get("reasons", []):
            print(f"   - 理由: {r}")
        if decision == case["expect"]:
            ok += 1
            print("  ✅ 通过")
        else:
            print("  ❌ 不通过")
    print(f"\n结果: {ok}/{len(CASES)} 通过")
    if ok == len(CASES):
        print("ALL_DONE")


if __name__ == "__main__":
    main()
