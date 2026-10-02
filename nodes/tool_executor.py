from tools.calculator import calculate
from tools.datetime_tool import get_current_datetime
from tools.notes import save_note, get_notes
from state import AgentState

import logging 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOLS = {
    "calculator": calculate,
    "datetime": get_current_datetime,
    "save_note": save_note,
    "get_notes": get_notes,
}

def execute_tool(state: AgentState) -> dict:
    tool_name = state.get("selected_tool")
    tool_input = state.get("tool_input")

    if tool_name not in TOOLS:
        return {"tool_result": "This requested action is not supported."}

    tool_function = TOOLS[tool_name]

    if tool_name in ("calculator", "save_note"):
        if tool_input is None:
            return {"tool_result": f"No input was provided for the {tool_name} tool."}
        logger.info(f"Executing tool '{tool_name}' with input: {tool_input}")
        result = tool_function(tool_input)
    else:
        logger.info(f"Executing tool '{tool_name}' without input.")
        result = tool_function()

    return {"tool_result": result}
