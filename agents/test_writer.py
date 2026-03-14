from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

Test_Writer = ChatPromptTemplate.from_template(
    """You are the Test Writer. 
    Write comphrehensive unit test for the code below. 
    
    Rules:
    -Use pytest.
    -Output ONLY the test file code (single file).
    -DO NOT include markdown fences.
    -Prefer pure unit tests; mock external I/O if needed. 
    -Use clear test names. 
    -If code requires input(), refactor the assumption: tests should import functions rather than rely on CLI input.
    
    Spec:
    {spec}

    Code:
    {code}
    """
)

def write_tests(llm, spec: str, code: str) -> str:
    """Use the Test Writer agent to write tests for the code."""
    chain = Test_Writer | llm | StrOutputParser()
    return chain.invoke({"spec": spec, "code": code}).strip()

