import os
import mlflow
from typing import Annotated
from typing_extensions import TypedDict
from langchain_community.tools import DuckDuckGoSearchResults
import langchain.chat_models
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.prompts import ChatPromptTemplate


class State(TypedDict):
    query: str
    messages: Annotated[list, add_messages]


def create(model_id: str, prompt: str) -> StateGraph:
    """ """

    # create agent with tools

    # TODO these search results are no good, I would like the same as smolagents
    tool = DuckDuckGoSearchResults(max_results=10)
    llm = langchain.chat_models.init_chat_model(
        f"openai:{model_id}",
        base_url=os.environ["OPENAI_API_BASE"],
        temperature=0.1,
    ).bind_tools([tool])

    def chatbot(state: State):
        return {
            "query": state["query"],
            "messages": [llm.invoke(state["messages"])],
        }

    tool_node = ToolNode(tools=[tool])

    # create system prompt template

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", prompt),
            ("human", "{input}"),
        ]
    )

    def sysprompt(state: State):
        return {
            "query": state["query"],
            "messages": prompt_template.invoke({"input": state["query"]}).messages,
        }

    # create graph

    graph_builder = StateGraph(State)

    # nodes
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_node("sysprompt", sysprompt)

    # edges
    graph_builder.add_edge(START, "sysprompt")
    graph_builder.add_edge("sysprompt", "chatbot")
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    # Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_edge("tools", "chatbot")

    return graph_builder.compile()


class Model(mlflow.pyfunc.ChatAgent):
    def __init__(self, model_id="hyper-hound", prompt="prompts:/hyper-hound@champion"):
        p = mlflow.load_prompt(prompt).template
        self.graph = create(model_id, p)

    def predict(self, ctx, model_input, params=None):
        return self.graph.invoke(model_input)
