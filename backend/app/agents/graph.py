import logging
from typing import Any, Dict, Literal
from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    hybrid_rag_node,
    improver_node,
    interview_tips_node,
    merger_node,
    parser_node,
)
from app.agents.state import HireWiseState
from app.schemas import HireWiseAnalysisResult, JobDescription

logger = logging.getLogger("hirewise.graph")


def route_score_threshold(state: HireWiseState) -> Literal["improver_node", "interview_tips_node"]:
    """
    Conditional Router: Checks if ATS score is below 80%.
    - If score < 80%: route to improver_node (Agent 3A) for STAR rewrites
    - If score >= 80%: route to interview_tips_node (Agent 3B) for coaching tips
    """
    score = state.get("ats_score", 0.0)
    logger.info(f"Conditional Routing Evaluation: Calculated ATS Score = {score}%")
    if score < 80.0:
        return "improver_node"
    return "interview_tips_node"


def build_hirewise_graph():
    """
    Constructs and compiles the HireWise LangGraph StateGraph workflow.
    """
    workflow = StateGraph(HireWiseState)

    # 1. Add all functional nodes
    workflow.add_node("parser_node", parser_node)
    workflow.add_node("hybrid_rag_node", hybrid_rag_node)
    workflow.add_node("improver_node", improver_node)
    workflow.add_node("interview_tips_node", interview_tips_node)
    workflow.add_node("merger_node", merger_node)

    # 2. Add linear pipeline edges
    workflow.add_edge(START, "parser_node")
    workflow.add_edge("parser_node", "hybrid_rag_node")

    # 3. Add conditional routing edge based on ATS score threshold
    workflow.add_conditional_edges(
        "hybrid_rag_node",
        route_score_threshold,
        {
            "improver_node": "improver_node",
            "interview_tips_node": "interview_tips_node"
        }
    )

    # 4. Join branches back to merger_node
    workflow.add_edge("improver_node", "merger_node")
    workflow.add_edge("interview_tips_node", "merger_node")
    workflow.add_edge("merger_node", END)

    return workflow.compile()


# Pre-compile the LangGraph executable
hirewise_graph = build_hirewise_graph()


async def execute_hirewise_workflow(
    pdf_bytes: bytes,
    job_description: JobDescription,
    raw_text: str = "",
    user_id: Optional[str] = None,
    file_hash: str = ""
) -> HireWiseAnalysisResult:
    """
    Executes the autonomous multi-agent pipeline asynchronously.
    """
    initial_state: HireWiseState = {
        "pdf_bytes": pdf_bytes,
        "file_hash": file_hash,
        "raw_text": raw_text,
        "job_description": job_description,
        "user_id": user_id,
        "agent_logs": []
    }

    final_state = await hirewise_graph.ainvoke(initial_state)
    return final_state["final_result"]

