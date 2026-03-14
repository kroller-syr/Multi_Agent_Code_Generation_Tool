from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

Documenter = ChatPromptTemplate.from_template(
    """You are the Documenter. 
    Generate concise documentation for the procedural program. 
    
    Rules: 
    -Output ONLY markdown for a README.
    -Include: Overview, How to Run, Example Usage, Design Notes, Testing.
    -Keep it crisp and accurate. 
    
    Spec:
    {spec}
    """
)

def write_docs(llm, spec: str) -> str:
    """Use the Documenter agent to write documentation from the spec."""
    chain = Documenter | llm | StrOutputParser()
    return chain.invoke({"spec": spec}).strip()

