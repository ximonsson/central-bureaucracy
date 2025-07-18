import dotenv
import os
import pathlib
from .db import connect
from .bots import init_hyperhound
from .io import run as runio

dotenv.load_dotenv()
home = pathlib.Path.home()
DB = os.environ.get("CENTRAL_BUREAUCRACY_DB", home / "data/m47rix.duckdb")


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
