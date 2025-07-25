import base64
import os
from mistralai import Mistral
import agents
import openai


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


def agent(model: str, instr: str, temp: float = 0.0):
    """
    Creates an agent with the specified model, instructions, and temperature.

    Args:
        model (str): The model to use for the agent.
        instr (str): The instructions for the agent.
        temp (float, optional): The temperature for the model. Defaults to 0.0.

    Returns:
        agents.Agent: The created agent.
    """

    c = openai.AsyncOpenAI(base_url=os.environ["OPENAI_API_BASE"])
    m = agents.OpenAIChatCompletionsModel(openai_client=c, model=model)

    return agents.Agent(
        model=m,
        name="Ink Inspector 7000",
        instructions=instr,
        model_settings=agents.ModelSettings(temperature=temp),
        tools=[],
    )
