from langchain_core.messages import SystemMessage, HumanMessage

from state import AgentState
from services.gemini import get_llm
from prompts import get_responder_prompt


llm = get_llm()


def _format_state(state: AgentState) -> str:
    return f"""
user_text: {state["user_text"]}
route: {state["route"]}
response_mode: {state["response_mode"]}
selected_tool: {state.get("selected_tool")}
tool_result: {state.get("tool_result")}
"""


def response_node(state: AgentState) -> dict:
    messages = [
        SystemMessage(content=get_responder_prompt()),
        HumanMessage(content=_format_state(state))
    ]

    response = llm.invoke(messages)

    return {"response_text": response.content}
