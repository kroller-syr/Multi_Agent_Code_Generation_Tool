from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

Peer_Programmer = ChatPromptTemplate.from_template(
    """You are the Peer Programmer. 
    Write clean, production level code that satisfies the spec. 
    Rules:
    -Output ONLY the python code for a single file program. 
    -Include a main() and if __name__ == "__main__": main()
    -Use Type Hints. 
    -Include docstrings. 
    -Include basic error handling.
    -DO NOT inlclude markdown fences
    
    Spec:
    {spec}
    """
)

#Apply reviewer fixes in one pass (simple patch agent)
Patcher = ChatPromptTemplate.from_template(
    """ You are the Patcher. 
    Revise the code to address the review comments.
    
    Rules: 
    -Output ONLY the full update Python code for the single file program. 
    -DO NOT include markdown fences.
    -Preserve good structure, make minimal changes necessary. 
    
    Spec: 
    {spec}
    
    Original Code:
    {code}
    
    Review Comments: 
    {review}
    """
)

def write_code(llm, spec: str) -> str:
    """Use the Peer Programmer agent to write code from the spec."""
    chain = Peer_Programmer | llm | StrOutputParser()
    return chain.invoke({"spec": spec}).strip()

def patch_code(llm, spec: str, code: str, review: str) -> str:
    """Use the Patcher agent to apply review feedback to the code."""
    chain = Patcher | llm | StrOutputParser()
    return chain.invoke({"spec": spec, "code": code, "review": review}).strip()
