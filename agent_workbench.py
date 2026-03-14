#agent_workbench.py
"""
LangChain + OpenAI "multi-agent" code workbench.

Agents:
- Prompt Refiner: clarifies and tightens the user's request.
- Peer Programmer: drafts implementation code.
- Code Reviewer: reviews and suggests fixes.
- Test Writer: writes unit tests.
- Documenter: produces concise documentation.

Outputs (written to project root):
- generated_app.py
- test_generated_app.py
- README_GENERATED.md
"""

from __future__ import annotations
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Union
from datetime import datetime

from agents.prompt_refiner import refine_request
from agents.peer_programmer import write_code, patch_code
from agents.code_reviewer import review_code
from agents.test_writer import write_tests
from agents.documenter import write_docs

from utils.text_utils import strip_code_fences
from utils.io_utils import make_output_paths, write_text_file

#Configuration 
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.4")
TEMPERATURE= 0.2



@dataclass
class WorkbenchArtifacts:
    refined_request: str
    code: str
    review: str
    tests: str
    docs: str

#Helpers
def ensure_api_key_loaded() -> None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please set it in your .env file.")
    
#Chains
def build_llm() -> ChatOpenAI:
    return ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)

def run_workbench(user_request: str, apply_one_review_fix_pass: bool = True) -> WorkbenchArtifacts:
    llm = build_llm()
    
    spec = refine_request(llm, user_request)

    code = strip_code_fences(write_code(llm, spec))

    review = review_code(llm, spec, code)

    if apply_one_review_fix_pass and review != "CODE_IS_PERFECT":
        code = strip_code_fences(patch_code(llm, spec, code, review))
        review2 = review_code(llm, spec, code)
        review = f"{review}\n\n--- AFTER PATCH RE-REVIEW ---\n{review2}"

    tests = strip_code_fences(write_tests(llm, spec, code))
    docs = write_docs(llm, spec)

    return WorkbenchArtifacts(
        refined_request=spec,
        code=code,
        review=review,
        tests=tests,
        docs=docs,
    )


def main() -> None:
    ensure_api_key_loaded()

    print("=== Agent Workbench ===")
    print("Describe the code you want to make. Example: 'A CLI todo app that stores tasks in a JSON file.'")
    user_request = input("\nWhat do you want to build? ").strip()
    if not user_request:
        print("No request provided. Exiting.")
        return

    artifacts = run_workbench(user_request=user_request, apply_one_review_fix_pass=True)

    code_path, test_path, readme_path = make_output_paths()
    write_text_file(code_path, artifacts.code)
    write_text_file(test_path, artifacts.tests)
    write_text_file(readme_path, artifacts.docs)

    print("\n=== Reviewer Notes ===")
    print(artifacts.review)

    print("\nDone. Run your generated app with:")
    print(f"  python {code_path.name}")
    print("\nRun tests with:")
    print(f"  pytest -q {test_path.name}")


if __name__ == "__main__":
    main()