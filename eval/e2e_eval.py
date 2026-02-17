import asyncio
import sys
from pathlib import Path
from typing import Dict, List

# Allow running this file directly from the eval/ directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.db import init_db
from app.workflows.qa_graph import run_qa_workflow

# ----------------------------
# Golden test cases
# ----------------------------

TEST_CASES: List[Dict] = [
    {
        "question": "What are my key skills?",
        "should_have_citation": True,
        "should_not_say_idk": True,
    },
    {
        "question": "What companies have I worked for?",
        "should_have_citation": True,
        "should_not_say_idk": True,
    },
    {
        "question": "What is the population of Mars?",
        "should_have_citation": False,
        "should_not_say_idk": False,
    },
    {
        "question": "Multiply 12 and 7",
        "should_have_citation": False,
        "should_not_say_idk": True,
    },
]

async def evaluate():
    init_db()

    total = len(TEST_CASES)
    passed = 0
    hallucinations = 0

    for case in TEST_CASES:
        result = await run_qa_workflow(
            case["question"],
            request_id="eval",
            client_key="eval"
        )

        answer = result.get("answer", "")
        citations = result.get("citations", [])

        has_citation = len(citations) > 0
        said_idk = "I don't know based on the provided documents." in answer

        ok = True

        # Citation enforcement
        if case["should_have_citation"] and not has_citation:
            ok = False

        # No hallucination rule
        if not case["should_have_citation"] and not said_idk and "Mars" in case["question"]:
            hallucinations += 1
            ok = False

        if ok:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"\nQ: {case['question']}")
        print(f"Status: {status}")
        print(f"Answer: {answer}")
        print(f"Citations: {citations}")

    print("\n----------------------------")
    print(f"Passed: {passed}/{total}")
    print(f"Hallucinations: {hallucinations}")


if __name__ == "__main__":
    asyncio.run(evaluate())
