from datetime import datetime, timedelta, timezone

from retell import Retell
from retell.resources.call import CallResource, CreateWebCallResponse
from app.config import (
    ADDITIONAL_CONTEXT_FROM_RAG,
    AGENT_GENDER,
    COMPANY_NAME,
    RETELL_API_KEY,
    RETELL_AGENT_ID,
)


retell_client = Retell(api_key=RETELL_API_KEY)
call_resource = CallResource(retell_client)
INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def get_call(call_id: str) -> dict:
    """Retrieve the current complete call using the official Retell SDK."""
    call = call_resource.retrieve(call_id=call_id)
    return call.model_dump() if hasattr(call, 'model_dump') else dict(call)


def create_web_call(
    customer_name: str,
    language_to_speak: str,
    agent_name: str,
    profile_id: str,
    dynamic_variables: dict[str, str] | None = None,
    metadata: dict | None = None,
) -> dict:
    """Create a new Retell web call with dynamic variables."""
    now = datetime.now(INDIA_TIMEZONE)
    variables = {
        **(dynamic_variables or {}),
        "company_name": COMPANY_NAME,
        "customer_name": customer_name,
        "agent_name": agent_name,
        "agent_gender": AGENT_GENDER,
        "current_date": now.strftime("%d %B %Y"),
        "current_day": now.strftime("%A"),
        "current_time": now.strftime("%I:%M %p"),
        "additional_context_from_rag": ADDITIONAL_CONTEXT_FROM_RAG,
        "language_to_speak": language_to_speak,
        "conversation_history": "",
        "customer_utterance": "",
    }

    response: CreateWebCallResponse = call_resource.create_web_call(
        agent_id=RETELL_AGENT_ID,
        retell_llm_dynamic_variables=variables,
        metadata={**(metadata or {}), "profile_id": profile_id},
    )
    return {
        "call_id": response.call_id,
        "access_token": response.access_token,
        "transport": response.transport,
        "ice_servers": [server.model_dump() for server in response.ice_servers]
        if response.ice_servers
        else None,
    }
