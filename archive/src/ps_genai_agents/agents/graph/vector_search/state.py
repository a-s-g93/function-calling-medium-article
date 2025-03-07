import operator
from typing import Annotated, Any, List, TypedDict, Union

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    # The input string
    input: str
    # The sub questions identified in the user input
    sub_questions: Annotated[Union[List[str], None], operator.add]
    # The list of previous messages in the conversation
    chat_history: list[BaseMessage]
    # The outcome of a given call to the agent
    # Needs `None` as a valid type, since this is what this will start as
    agent_outcome: Union[AgentAction, AgentFinish, None]
    # List of actions and corresponding observations
    # Here we annotate this with `operator.add` to indicate that operations to
    # this state should be ADDED to the existing values (not overwrite it)
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]
    # The vector search source node IDs
    sources: Annotated[Union[List[Any], None], operator.add]
    # The context retrieved
    context: Annotated[Union[List[Any], None], operator.add]
