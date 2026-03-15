# Agent Workbench (LangChain + OpenAI)

A lightweight “multi-agent” code generation workbench that uses LangChain + OpenAI to 
help you **spec**, **write**, **review**, **test**, and **document** Python programs from a single prompt.

It runs as a CLI script, asks what you want to build, then orchestrates five specialized agents:

- **Prompt Refiner** – turns your request into a crisp implementation spec
- **Peer Programmer** – generates a production-quality Python implementation
- **Code Reviewer** – finds issues and suggests improvements
- **Test Writer** – generates pytest unit tests
- **Documenter** – generates a README-style document

Outputs are written to timestamped files in the project root so runs don’t overwrite each other.

---

## Features

- Terminal-driven workflow (`agent_workbench.py`)
- Uses OpenAI via LangChain (`ChatOpenAI`)
- Automatic “review + patch” pass (one iteration) to improve generated code
- Timestamped outputs per run:
  - `generated_app_YYYYMMDD_HHMMSS.py`
  - `test_generated_app_YYYYMMDD_HHMMSS.py`
  - `README_GENERATED_YYYYMMDD_HHMMSS.md`

## Included 2 Generated Apps as POC
generated_app_OCR_TextExtraction.py
&
generated_app_int_squares.py
Were both generated using the Multi-Agent Code Generation tool, included in repo to showcase basic functionality and 
operation of app, both include readme and unit test for code. 
*300zx sample pdf and 300zx sample md are input/output from the OCR TextExtraction to showcase operational capability of generated code
using the agent_workbench.py
---


## Requirements

- Python 3.11+ (3.12 recommended)
- An OpenAI API key

---

## Setup

### 1) Create & activate venv (Windows / PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel

#Dependencies
python -m pip install -U langchain langchain-openai python-dotenv pydantic

#Running the project/app
python agent_workbench.py

#Once code is completed generates a unique name using a timestamp, to run the generated app:
python generated_app_YYYYMMDD_HHMMSS.py

#If using the code to generate a streamlit app use this to run the generated app:
python -m pip install -U streamlit
streamlit run generated_app_YYYYMMDD_HHMMSS.py

#Project Structure
Goal Setting and Monitoring/
├─ agent_workbench.py
├─ agents/
│  ├─ __init__.py
│  ├─ prompt_refiner.py
│  ├─ peer_programmer.py
│  ├─ code_reviewer.py
│  ├─ test_writer.py
│  └─ documenter.py
├─ utils/
│  ├─ __init__.py
│  ├─ io_utils.py
│  └─ text_utils.py
├─ .env
└─ .venv/
