from typing import TypedDict , Literal ,  NotRequired
from pydantic import BaseModel

class AgentState(TypedDict):
    user_text: str

    route: NotRequired[str]
    response_mode: NotRequired[str]
    selected_tool: NotRequired[str | None]
    tool_input: NotRequired[str | None]
    tool_result: NotRequired[str | list[str] | None]
    response_text: NotRequired[str]

    
class RouterDecision(BaseModel):
    route: Literal["tool" , "llm"]
    response_mode: Literal["text" , "speech"]
    selected_tool: Literal[
        "calculator",
        "datetime",
        "save_note",
        "get_notes"
    ] | None
    tool_input: str | None
