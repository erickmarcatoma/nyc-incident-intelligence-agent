import json

from backend.agent import run_agent
from backend.schemas import Borough


def run_case(question: str, borough: Borough) -> None:
    trace = {
        "question": question,
        "borough": borough.value,
        "final_answer": run_agent(borough),
    }
    print(json.dumps(trace, indent=2))


if __name__ == "__main__":
    run_case("What collision reports are available?", Borough.QUEENS)