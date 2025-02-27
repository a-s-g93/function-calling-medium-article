"""LangGraph edges that are used in multiple workflows."""

from typing import List, Literal

from langgraph.types import Send

from ...components.state import OverallState, ToolSelectionOutputState
from ...components.text2cypher.state import CypherOutputState


def guardrails_conditional_edge(
    state: OverallState,
) -> Literal["planner", "final_answer"]:
    match state.get("next_action"):
        case "final_answer":
            return "final_answer"
        case "end":
            return "final_answer"
        case "planner":
            return "planner"
        case _:
            return "final_answer"


def tool_select_conditional_edge(
    state: OverallState,
) -> Literal["summarize", "final_answer"]:
    match state.get("next_action"):
        case "summarize":
            return "summarize"
        case "final_answer":
            return "final_answer"
        case _:
            return "final_answer"


def validate_final_answer_router(
    state: OverallState,
) -> Send:
    match state.get("next_action"):
        case "final_answer":
            return Send("final_answer", state)
        case "text2cypher":
            # currently only allow for a single follow up question at a time
            tasks = state.get("tasks", list())
            new_task = tasks[-1]
            return Send("text2cypher", {"task": new_task.question})
        case _:
            return Send("final_answer", state)


def query_mapper_edge(state: OverallState) -> List[Send]:
    """Map each task question to a Text2Cypher subgraph."""

    return [
        Send("text2cypher", {"task": task.question})
        for task in state.get("tasks", list())
    ]


def map_reduce_planner_to_tool_selection(state: OverallState) -> List[Send]:
    """Map each identified task in the planner stage to a tool_selection node."""

    return [
        Send(
            "tool_selection",
            {
                "question": task.question,
                "parent_task": task.parent_task,
                "requires_visualization": task.requires_visualization,
            },
        )
        for task in state.get("tasks", list())
    ]


def tool_selection_output_router(state: ToolSelectionOutputState) -> Send:
    print("in router")
    match state.get("next_action", ""):
        case "text2cypher":
            return Send("text2cypher", {"task": state.get("task", "")})
        case "predefined_cypher":
            return Send(
                "predefined_cypher",
                {
                    "task": state.get("task", ""),
                    "tool_call": state.get("tool_call", dict()),
                },
            )
        case "error":
            return Send("final_answer", dict())
        case _:
            return Send("final_answer", dict())


def viz_mapper_edge(state: OverallState) -> List[Send]:
    """Map each sub question to a Visualize subgraph if a visual is required."""

    # need to check existing charts in case of follow up questions
    existing_chart_questions = [
        x.get("task", "") for x in state.get("visualizations", list())
    ]

    indexes = [
        idx
        for idx, task in enumerate(state.get("tasks", []))
        if task.requires_visualization and task.question not in existing_chart_questions
    ]

    tasks = list()
    for idx in indexes:
        try:
            cypher_state: CypherOutputState = state.get("cyphers", list())[idx]
            task = Send(
                "visualize",
                {
                    "task": cypher_state.get("task"),
                    "records": cypher_state.get("records"),
                },
            )
            tasks.append(task)

        except Exception as e:
            print(f"Viz mapper edge error: {e}")
            continue

    return tasks or [Send("gather_visualizations", state)]
