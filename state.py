from typing import TypedDict , Literal
from pydantic import BaseModel

class AgentState(TypedDict):
    user_text: str
    route: str
    response_mode: str
    selected_tool: str | None
    response_text: str


class RouterDecision(BaseModel):
    route: Literal["tool" , "llm"]
    response_mode: Literal["text" , "speech"]
    selected_tool: Literal[
        "calculator",
        "datetime",
        "save_note",
        "get_notes"
    ] | None


