from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

Code_Reviewer = ChatPromptTemplate.from_template(
    """You are the Code Reviewer. 
    Review the code for correctness, readability, and adherence to the spec.
    Critically analyze the code ahainst the spec, and identify bugs, missing cases, poor style and imporvements.

    Rules:
    -Output a concise review with:
    1. Summary of issues (if any) in bullet points
    2. If the code is perfect, say "Code looks good!"
    3. Be specific: refernce functions/sections. 
    
    Spec:
    {spec}
    
    Code:
    {code}
    """
)

def review_code(llm, spec: str, code: str) -> str:
    """Use the Code Reviewer agent to review the code against the spec."""
    chain = Code_Reviewer | llm | StrOutputParser()
    return chain.invoke({"spec": spec, "code": code}).strip()

