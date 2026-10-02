from langchain_core.messages import SystemMessage, HumanMessage

from state import AgentState , RouterDecision
from services.gemini import get_llm
from prompts import get_router_prompt
import logging


from google.api_core.exceptions import (
    ResourceExhausted,
    ServiceUnavailable,
    DeadlineExceeded,
)

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

llm = get_llm()
router_llm = llm.with_structured_output(RouterDecision)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable, DeadlineExceeded)),
    reraise=True,
)
def router_node(state: AgentState) -> dict:
    messages = [
        SystemMessage(content=get_router_prompt()),
        HumanMessage(content=state["user_text"])
    ]

    try:
        decision: RouterDecision = router_llm.invoke(messages)

        logger.info(
            "Router decision: route=%s tool=%s mode=%s",
            decision.route,
            decision.selected_tool,
            decision.response_mode,
        )

        return decision.model_dump()
    except (
        ResourceExhausted,
        ServiceUnavailable,
        DeadlineExceeded,
    ):
        logger.warning("Router LLM request failed, retrying...")
        raise
    except Exception as e:
        logger.error("Router LLM request failed: %s", str(e))
        raise
