"""
run_comparison.py — 3개 프레임워크 비교 실행기

실행:
  cd <repo_root>
  source .venv/bin/activate
  python examples/research_agent_comparison/run_comparison.py
"""
import sys, os, time, textwrap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib.util


def count_code_lines(filepath: str) -> int:
    """주석·빈 줄·docstring을 제외한 실제 코드 라인 수."""
    with open(filepath) as f:
        lines = f.readlines()
    in_docstring = False
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            # 같은 줄에서 열고 닫는 경우 (한 줄 docstring)
            if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                continue
            in_docstring = not in_docstring
            continue
        if in_docstring:
            continue
        if not stripped or stripped.startswith("#"):
            continue
        count += 1
    return count


def run_module(name: str, filepath: str):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BASE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = [
    ("LangChain create_agent",       "01_langchain_create_agent.py"),
    ("LangGraph StateGraph 수동",     "02_langgraph_manual.py"),
    ("LangGraph create_react_agent", "03_langgraph_prebuilt.py"),
]

print("=" * 60)
print("  3개 프레임워크 리서치 에이전트 비교")
print("  태스크: Python GIL 설명 및 우회 방법 정리")
print("=" * 60)
print()

results = []

for label, filename in EXPERIMENTS:
    filepath = os.path.join(BASE, filename)
    loc = count_code_lines(filepath)

    print(f"▶ {label}")
    print(f"  파일: {filename}  (코드 {loc} 줄)")

    t0 = time.perf_counter()
    mod = run_module(label, filepath)
    result = mod.run()
    elapsed = time.perf_counter() - t0

    msgs = result["messages"]
    final = msgs[-1].content

    print(f"  실행 시간: {elapsed:.3f}s")
    print(f"  총 메시지: {len(msgs)}개 {[type(m).__name__ for m in msgs]}")
    print(f"  최종 답변 (앞 120자):")
    print("    " + textwrap.shorten(final, width=120, placeholder="..."))
    print()

    results.append({
        "label": label,
        "loc": loc,
        "msg_count": len(msgs),
        "elapsed": elapsed,
        "answer_len": len(final),
    })

# ── 비교 표 ──────────────────────────────────────────────────
print("=" * 60)
print("  비교 표")
print("=" * 60)
header = f"{'프레임워크':<28} {'코드(LOC)':>9} {'메시지':>6} {'시간(s)':>8} {'답변길이':>8}"
print(header)
print("-" * 60)
for r in results:
    print(f"{r['label']:<28} {r['loc']:>9} {r['msg_count']:>6} {r['elapsed']:>8.3f} {r['answer_len']:>8}")
print()

print("※ 메시지 흐름: HumanMessage → AIMessage(tool_call) → ToolMessage → AIMessage(final)")
print("※ 3개 프레임워크 모두 동일한 4-메시지 루프 패턴 사용")
print()
print("⚠️  Deep Agents(04_deep_agents_stub.py)는 패키지 미설치로 제외됨")
