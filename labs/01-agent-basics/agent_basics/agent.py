"""ADK Agent definition for the order-support lab."""

from __future__ import annotations

import os

from google.adk.agents import Agent
from google.adk.apps import App

from .tools import estimate_shipping
from .tools import get_order_status


MODEL = os.getenv("ADK_MODEL", "gemini-3.5-flash")

root_agent = Agent(
    name="order_support_agent",
    model=MODEL,
    description=(
        "Answers read-only order-status questions and estimates shipping cost."
    ),
    instruction="""
You are a read-only order support agent.

- Use get_order_status for an order's current status. Never invent an order.
- Use estimate_shipping only after the user supplies a destination zone and
  package weight. Never calculate a shipping price yourself.
- Treat structured tool errors as expected outcomes. Explain the problem and
  ask only for the missing or corrected input.
- You cannot create, cancel, update, pay for, or ship an order. Never claim
  that a mutation happened.
- Keep the final answer concise and include units and currency when relevant.
""".strip(),
    tools=[
        get_order_status,
        estimate_shipping,
    ],
    mode="chat",
)

app = App(
    name="order_support",
    root_agent=root_agent,
)
