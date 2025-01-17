from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_neo4j import Neo4jGraph
from langgraph.constants import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph

from ..components.state import (
    CypherState,
    OverallState,
)
from ..components.text2cypher import (
    create_text2cypher_correction_node,
    create_text2cypher_execution_node,
    create_text2cypher_generation_node,
    create_text2cypher_validation_node,
)


def create_text2cypher_agent(
    llm: BaseChatModel, graph: Neo4jGraph, cypher_query_yaml_file_path: str = "./"
) -> CompiledStateGraph:
    """
    Create a Text2Cypher agent using LangGraph.
    This agent contains only Text2cypher components with no guardrails, query parser or summarizer.
    This agent may be used as an independent workflow or a node in a larger LangGraph workflow.

    Returns
    -------
    CompiledStateGraph
        The workflow.
    """

    generate_cypher = create_text2cypher_generation_node(
        llm=llm, graph=graph, cypher_query_yaml_file_path=cypher_query_yaml_file_path
    )
    validate_cypher = create_text2cypher_validation_node(llm=llm, graph=graph)
    correct_cypher = create_text2cypher_correction_node(llm=llm, graph=graph)
    execute_cypher = create_text2cypher_execution_node(graph=graph)

    text2cypher_graph_builder = StateGraph(
        CypherState, input=CypherState, output=OverallState
    )
    text2cypher_graph_builder.add_node(generate_cypher)
    text2cypher_graph_builder.add_node(validate_cypher)
    text2cypher_graph_builder.add_node(correct_cypher)
    text2cypher_graph_builder.add_node(execute_cypher)

    text2cypher_graph_builder.add_edge(START, "generate_cypher")
    text2cypher_graph_builder.add_edge("generate_cypher", "validate_cypher")
    text2cypher_graph_builder.add_conditional_edges(
        "validate_cypher",
        validate_cypher_conditional_edge,
    )
    text2cypher_graph_builder.add_edge("correct_cypher", "validate_cypher")
    text2cypher_graph_builder.add_edge("execute_cypher", END)

    return text2cypher_graph_builder.compile()


def validate_cypher_conditional_edge(
    state: CypherState,
) -> Literal["correct_cypher", "execute_cypher", "__end__"]:
    print(f"NEXT ACTION: {state.get("next_action_cypher")}")
    match state.get("next_action_cypher"):
        case "correct_cypher":
            return "correct_cypher"
        case "execute_cypher":
            return "execute_cypher"
        case "__end__":
            return "__end__"
        case _:
            return "__end__"
