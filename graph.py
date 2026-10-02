from langgraph.graph import StateGraph , START , END

from state import AgentState
from nodes.router import router_node
from nodes.tool_executor import execute_tool
from nodes.responder import response_node

def route_request(state: AgentState) -> str:
    return state["route"]

builder = StateGraph(AgentState)

builder.add_node("router" , router_node)
builder.add_node("tool_executor" , execute_tool)
builder.add_node("responder" , response_node)

builder.add_edge(START , "router")

builder.add_conditional_edges(
    "router" ,
    route_request ,
    {
        "tool" : "tool_executor" ,
        "llm" : "responder" ,
    } ,
)

builder.add_edge("tool_executor" , "responder")
builder.add_edge("responder" , END)


graph = builder.compile()