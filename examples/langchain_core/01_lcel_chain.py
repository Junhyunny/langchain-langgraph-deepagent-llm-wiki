"""LCEL | operator and Runnable primitives.

Shows:
- RunnableLambda wraps a plain function into the Runnable interface
- | creates a RunnableSequence (type inspection proves it)
- dict syntax creates RunnableParallel
- RunnableParallel results are a dict keyed by the mapping keys
"""

from __future__ import annotations

from langchain_core.runnables import RunnableLambda, RunnableParallel


def double(x: int) -> int:
    return x * 2


def add_ten(x: int) -> int:
    return x + 10


def main() -> None:
    # --- 1. RunnableLambda ---
    r = RunnableLambda(double)
    print("type:", type(r).__name__)          # RunnableLambda
    print("invoke(5):", r.invoke(5))          # 10

    # --- 2. RunnableSequence via | ---
    chain = RunnableLambda(double) | RunnableLambda(add_ten)
    print("\nchain type:", type(chain).__name__)   # RunnableSequence
    print("chain.invoke(3):", chain.invoke(3))     # double(3)=6, add_ten(6)=16

    # --- 3. RunnableParallel via dict shorthand ---
    parallel = RunnableParallel(
        doubled=RunnableLambda(double),
        added=RunnableLambda(add_ten),
    )
    print("\nparallel type:", type(parallel).__name__)  # RunnableParallel
    result = parallel.invoke(5)
    print("parallel.invoke(5):", result)  # {'doubled': 10, 'added': 15}

    # --- 4. Chaining parallel + lambda ---
    pipeline = parallel | RunnableLambda(lambda d: d["doubled"] + d["added"])
    print("\npipeline.invoke(5):", pipeline.invoke(5))  # 10 + 15 = 25


if __name__ == "__main__":
    main()
