from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

#Agent Prompts
Prompt_Refiner = ChatPromptTemplate.from_template(
    """You are the Prompt Reginer. 
    Your job: turn the user's rough request into a clear, unabmigous spec
    for a coding task.
    Rules:
    -Ask clarifying questions only if necessary to resolve ambigous requests, otherwise make assumptions instead. 
    -Output MUST be a compact specification with:
    1. Goal (1-2 sentences)
    2. Inputs
    3. Outputs
    4. Constraints (librairies, runtime, edge cases)
    5. Acceptance Criteria (bullet list)
    -Keep it under 250 lines.
    
    User Request:
    {user_request}
    """
)

def refine_request(llm, user_request: str) -> str:
    """Use the Prompt Refiner agent to clarify and tighten the user's request."""
    chain = Prompt_Refiner |llm | StrOutputParser()
    return chain.invoke({"user_request": user_request}).strip()

