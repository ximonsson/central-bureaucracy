import dotenv
import os
import pathlib
from .db import connect
from .io import run as runio
import mlflow
import hyperhound


dotenv.load_dotenv()
home = pathlib.Path.home()
DB = os.environ.get("CENTRAL_BUREAUCRACY_DB", home / "data/m47rix.duckdb")


def init_hyperhound(prompt_path: str):
    """
    Initialize Hyper Hound.

    Ags:
        prompt_path: path to the prompt file
    """

    if prompt_path.startswith("prompts:/"):
        prompt = mlflow.load_prompt(prompt_path).template
    else:
        with open(prompt_path) as f:
            prompt = f.read()

    model_id = "hyper-hound"

    return hyperhound.create_graph(model_id, prompt)


def main() -> None:
    if False:  # TODO while testing
        runio()

    if False:
        _ = connect(DB)

    prompt_path = os.environ.get(
        "CENTRAL_BUREAUCRACY_HYPER_HOUND_SYSPROMPT", "prompts:/hyper-hound@champion"
    )
    hh = init_hyperhound(prompt_path)
    y = hh.invoke({"query": "futurama-central-bureaucracy"})
    print(y["messages"][-1].content)
