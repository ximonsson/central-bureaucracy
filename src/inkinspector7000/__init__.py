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
    """
    Perform OCR on an image using the Mistral OCR model.

    Args:
        path (str): The path to the image file.
        model_id (str, optional): The ID of the OCR model to use. Defaults to "mistral-ocr-latest".

    Returns:
        dict: The OCR result.
    """

    img = encode(path)
    # client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    client = Mistral(server_url="http://localhost:4000/mistral/v1")

    res = client.ocr.process(
        model=model_id,
        document={
            "type": "image_url",
            "image_url": f"data:image/jpeg;base64,{img}",
        },
        include_image_base64=True,
    )

    return res


def transcribe(model: str, img_path: str):
    """
    Transcribes an image to markdown using a specified model.

    Args:
        model (str): The model to use for transcription.
        img_path (str): The path to the image to transcribe.

    Returns:
        The response from the transcription model.
    """

    c = openai.OpenAI(base_url=os.environ["OPENAI_API_BASE"])
    img = encode(img_path)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Transcribe this to markdown"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img}",
                    },
                },
            ],
        }
    ]
    res = c.chat.completions.create(model=model, messages=messages)
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
