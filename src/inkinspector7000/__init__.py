import base64
import os
from mistralai import Mistral
from typing import Annotated
from typing_extensions import TypedDict
import langchain.chat_models
from langgraph.graph.message import add_messages
from langgraph.graph import Graph, StateGraph, START, END


def encode(path: str) -> str:
    """Perform base64 encoding on image."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def ocr(path: str, model_id: str = "mistral-ocr-latest") -> dict:
    img = encode(path)
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    res = client.ocr.process(
        model=model_id,
        document={
            "type": "image_url",
            "image_url": f"data:image/jpeg;base64,{img}",
        },
        include_image_base64=True,
    )

    return res


class State(TypedDict):
    messages: Annotated[list, add_messages]


def graph(model_id: str, sysprompt: str):
    """
    Create graph
    """

    llm = langchain.chat_models.init_chat_model(
        f"openai:{model_id}",
        base_url=os.environ["OPENAI_API_BASE"],
        temperature=0.1,
    )

    def chatbot(impath):
        # return ocr(impath)

        im = encode(impath)
        msg = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Transcribe this."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{im}"},
                    },
                ],
            }
        ]

        return {
            "messages": [llm.invoke(msg)],
        }

    graph_builder = Graph()
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)

    return graph_builder.compile()
