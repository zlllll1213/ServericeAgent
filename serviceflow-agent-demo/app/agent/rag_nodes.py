from __future__ import annotations

from app.agent.nodes_helpers import trace_step as _trace
from app.agent.nodes_support import generate_rag_answer as _generate_rag_answer
from app.agent.state import AgentState
from app.rag.service import retrieve_documents


def rag_node(state: AgentState) -> AgentState:
    docs = retrieve_documents(state["user_message"], intent=state.get("intent", "UNKNOWN"), top_k=3)
    answer_payload = _generate_rag_answer(state["user_message"], docs)
    return {
        **state,
        "retrieved_docs": docs,
        "citations": answer_payload["citations"],
        "final_answer": answer_payload["answer"],
        "route_trace": _trace(state, "rag_node"),
    }

