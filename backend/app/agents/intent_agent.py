"""
Intent Agent — extracts structured job-search intent from a natural-language query.
Uses OpenAI structured outputs (gpt-4o-mini) with Pydantic validation.
"""
import os
from typing import Optional
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.core.config import settings


class IntentExtraction(BaseModel):
    """Validated intent extracted from a natural-language job request."""
    intent: str = Field(
        description="One of: search_and_apply, search_only, open_and_apply, fill_only, continue_application, review_application"
    )
    company: Optional[str] = Field(None, description="Target company name if specified")
    role: Optional[str] = Field(None, description="Job role or title")
    location: Optional[str] = Field(None, description="Preferred location (city, country, or 'remote')")
    experience_level: Optional[str] = Field(None, description="Entry level, Mid, Senior, etc.")
    employment_type: Optional[str] = Field(None, description="Full-time, Part-time, Internship, Contract")
    work_mode: Optional[str] = Field(None, description="Remote, On-site, Hybrid")
    skills: list[str] = Field(default_factory=list, description="Technologies or skills mentioned")
    job_url: Optional[str] = Field(None, description="Direct URL if provided by user")


INTENT_SYSTEM_PROMPT = """You are FormPilot AI's intent extraction engine.
A user will give you a natural-language job search or application request.
Extract structured information from it. 

Intent types:
- search_and_apply: user wants to find a job and fill the application form
- search_only: user only wants to find/browse jobs
- open_and_apply: user provides a URL directly and wants to fill the form
- fill_only: the form is already open, just fill it
- continue_application: resume a previous session
- review_application: review what was already filled

Be precise. If the user says "find and apply" it's search_and_apply.
If they give a URL directly, it's open_and_apply.
Extract only what is explicitly mentioned — do not infer aggressively.
"""


async def run_intent_agent(state: AgentState) -> AgentState:
    """Parse the user query and extract structured intent."""
    query = state["user_query"]
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
        ).with_structured_output(IntentExtraction)
        
        result: IntentExtraction = await llm.ainvoke([
            SystemMessage(content=INTENT_SYSTEM_PROMPT),
            HumanMessage(content=query),
        ])
        
        intent_dict = result.model_dump()
        state["intent"] = intent_dict
        state["current_node"] = "parse_request"
        state["messages"].append({
            "type": "agent_message",
            "node": "parse_request",
            "text": f"Understood: Looking for **{result.role or 'a role'}** at **{result.company or 'any company'}**"
                    + (f" in {result.location}" if result.location else "")
                    + f" [{result.intent}]",
        })
        
    except Exception as e:
        # Fallback: simple keyword extraction without LLM
        intent_dict = _fallback_intent(query)
        state["intent"] = intent_dict
        state["messages"].append({
            "type": "agent_message",
            "node": "parse_request",
            "text": f"Parsed request (offline mode): {query}",
        })
        state["current_node"] = "parse_request"
    
    return state


def _fallback_intent(query: str) -> dict:
    """Simple keyword-based fallback if LLM is unavailable."""
    q = query.lower()
    intent = "search_and_apply"
    if "http" in q or "www." in q:
        intent = "open_and_apply"
    elif "find" in q and "apply" not in q:
        intent = "search_only"
    elif "continue" in q or "resume" in q:
        intent = "continue_application"
    
    return {
        "intent": intent,
        "company": None,
        "role": None,
        "location": None,
        "experience_level": None,
        "employment_type": None,
        "work_mode": None,
        "skills": [],
        "job_url": None,
    }
