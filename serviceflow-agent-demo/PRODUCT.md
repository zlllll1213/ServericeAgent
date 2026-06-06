# Product

## Register

product

## Users
Demo operators, solution engineers, and product stakeholders evaluating an enterprise customer-service agent. They use the app locally to test customer questions, inspect routing decisions, and understand how the agent combines workflow routing, business data, tools, knowledge retrieval, and human handoff.

## Product Purpose
ServiceFlow Agent Demo shows that an enterprise support agent is more than ordinary RAG. It classifies intent, routes each request through a LangGraph workflow, queries SQLite business data, calls simulated ERP tools, retrieves from typed knowledge bases, creates human tickets for escalation, and returns a visible decision trace for demos.

## Brand Personality
Clear, operational, and credible. The product should feel like a working service console: direct, inspectable, calm under pressure, and built for explaining agent decisions rather than hiding them.

## Anti-references
Avoid a generic chatbot landing page, decorative SaaS hero metrics, opaque AI magic, fake glassmorphism, overbuilt admin chrome, and designs that bury routing evidence behind tabs. The trace and tool calls are the core demo value.

## Design Principles
- Show the workflow, not just the answer.
- Keep the first version locally runnable and easy to extend.
- Separate routing, tools, retrieval, database, and web UI so later upgrades are natural.
- Make degraded mode useful when no LLM API key is configured.
- Treat low confidence and complaints as operational events that create tickets.

## Accessibility & Inclusion
Aim for WCAG 2.1 AA contrast, keyboard-operable controls, visible focus states, readable Chinese interface copy, reduced-motion-safe UI, and error messages shown next to the chat action.
