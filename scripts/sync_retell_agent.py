"""Apply the versioned LAP prompt and extraction fields to the Retell agent."""

import os
from pathlib import Path

from dotenv import load_dotenv
from retell import Retell


PROMPT_PATH = Path(__file__).parents[1] / "app" / "prompts" / "lap_agent.txt"

ANALYSIS_FIELDS = [
    {"type": "system-presets", "name": "call_summary"},
    {"type": "system-presets", "name": "call_successful"},
    {"type": "system-presets", "name": "user_sentiment"},
    {
        "type": "enum",
        "name": "call_outcome",
        "description": "Final call outcome",
        "choices": ["qualified", "disqualified", "transfer", "callback", "not_interested", "wrong_person", "incomplete"],
    },
    {
        "type": "boolean",
        "name": "original_documents",
        "description": "Whether original property documents are available",
    },
    *[
        {"type": "number", "name": name, "description": description}
        for name, description in {
            "loan_amount": "Accepted loan amount in INR",
            "market_value": "Estimated property market value in INR",
            "tenure_years": "Requested tenure in years",
        }.items()
    ],
    *[
        {"type": "string", "name": name, "description": description}
        for name, description in {
            "property_type": "Residential, commercial, industrial, or agricultural",
            "ownership_status": "Sole or joint",
            "occupation": "Salaried or self-employed",
            "income_mode": "Bank or cash",
            "callback_time": "Requested callback time",
            "disqualification_reason": "Reason the customer failed eligibility",
            "transfer_reason": "Existing property loan or EMI reduction request",
        }.items()
    ],
]


def main() -> None:
    load_dotenv()
    api_key = os.environ["RETELL_API_KEY"]
    agent_id = os.environ["RETELL_AGENT_ID"]
    client = Retell(api_key=api_key)
    agent = client.agent.retrieve(agent_id)
    response_engine = agent.response_engine
    if response_engine.type != "retell-llm":
        raise RuntimeError("Agent must use a Retell LLM response engine")

    client.llm.update(
        response_engine.llm_id,
        general_prompt=PROMPT_PATH.read_text(encoding="utf-8"),
    )
    update = {
        "post_call_analysis_data": ANALYSIS_FIELDS,
        "webhook_events": [
            "call_started",
            "transcript_updated",
            "call_ended",
            "call_analyzed",
        ],
    }
    public_base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    if public_base_url:
        update["webhook_url"] = f"{public_base_url}/webhooks/retell"
    client.agent.update(agent_id, **update)
    print(f"Synced prompt and analysis configuration to agent {agent_id}")


if __name__ == "__main__":
    main()
