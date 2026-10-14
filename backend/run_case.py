import json
from pathlib import Path
from agent import run_agent

def load_fixture(name):
    return json.loads(Path(__file__).parent.joinpath("fixtures", f"{name}.json").read_text())

def run_case(fixture_name, question):
    trace = {"question": question, "tool_result": load_fixture(fixture_name)}
    trace["final_answer"] = run_agent(question, trace["tool_result"])
    print(json.dumps(trace, indent=2))

run_case("injection_incident", "Any incidents in Queens?")