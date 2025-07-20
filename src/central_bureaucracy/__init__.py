import dotenv
import os
import pathlib
from .db import connect  # noqa
from .io import run as runio, tags  # noqa
import mlflow
import hyperhound
import inkinspector7000
import codeclerk
from langgraph.graph import Graph, START, END
import logging
import arxiv
import re

# setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("central-bureaucracy")
log.setLevel(logging.DEBUG)

dotenv.load_dotenv()
home = pathlib.Path.home()

DB = os.environ.get("CENTRAL_BUREAUCRACY_DB", "data.duckdb")
PATH = os.environ.get("CENTRAL_BUREAUCRACY_PATH", "/tmp/cb")

# hyper hound

SYSPROMPT_HYPER_HOUND = os.environ.get(
    "CENTRAL_BUREAUCRACY_HYPER_HOUND_SYSPROMPT", "prompts:/hyper-hound@champion"
)
MODELID_HYPER_HOUND = os.environ.get(
    "CENTRAL_BUREAUCRACY_HYPER_HOUND_MODELID", "hyper-hound"
)

# ink inspector 7000

SYSPROMPT_INK_INSPECTOR_7000 = os.environ.get(
    "CENTRAL_BUREAUCRACY_INK_INSPECTOR_7000_SYSPROMPT",
    "prompts:/ink-inspector-7000@champion",
)
MODELID_INK_INSPECTOR_7000 = os.environ.get(
    "CENTRAL_BUREAUCRACY_INK_INSPECTOR_7000_MODELID", "ink-inspector-7000"
)

# code clerk

SYSPROMPT_CODE_CLERK = os.environ.get(
    "CENTRAL_BUREAUCRACY_CODE_CLERK_SYSPROMPT", "prompts:/code-clerk@champion"
)
MODELID_CODE_CLERK = os.environ.get(
    "CENTRAL_BUREAUCRACY_CODE_CLERK_MODELID", "code-clerk"
)


def init_hyperhound(prompt_path: str):
    """
    Initialize Hyper Hound.

    Args:
        prompt_path str: path to the prompt file
    """

    log.info("Initialize Hyper Hound...")
    log.debug("Prompt: %s", prompt_path)
    log.debug("Model ID: %s", MODELID_HYPER_HOUND)

    if prompt_path.startswith("prompts:/"):
        prompt = mlflow.load_prompt(prompt_path).template
    else:
        with open(prompt_path) as f:
            prompt = f.read()

    return hyperhound.create_graph(MODELID_HYPER_HOUND, prompt)


def init_inkinspector(prompt_path: str):
    """
    Initialize Ink Inspector.

    Args:
        prompt_path str: path to the prompt file
    """

    log.info("Initialize Ink Inspector 7000...")
    log.debug("Prompt: %s", prompt_path)
    log.debug("Model ID: %s", MODELID_INK_INSPECTOR_7000)

    if prompt_path.startswith("prompts:/"):
        prompt = mlflow.load_prompt(prompt_path).template
    else:
        with open(prompt_path) as f:
            prompt = f.read()

    return inkinspector7000.graph(MODELID_INK_INSPECTOR_7000, prompt)


def init_codeclerk(prompt_path: str):
    """
    Initialize Ink Inspector.

    Args:
        prompt_path str: path to the prompt file
    """

    log.info("Initialize Code Clerk...")
    log.debug("Prompt: %s", prompt_path)
    log.debug("Model ID: %s", MODELID_CODE_CLERK)

    if prompt_path.startswith("prompts:/"):
        prompt = mlflow.load_prompt(prompt_path).template
    else:
        with open(prompt_path) as f:
            prompt = f.read()

    return codeclerk.graph(MODELID_HYPER_HOUND, prompt)


def create_arxiv_note(query: dict):
    """Create a note from an arXiv paper."""

    # filename should be the arxiv ID
    path = query["path"]
    filename = pathlib.Path(path).stem

    log.info("Query arXiv: %s", filename)

    content = arxiv.create_note(filename)
    query["result"] = content

    return query


def cmd(tags: list[str]) -> str | None:
    """
    Extracts the command from a list of tags.

    Args:
        tags (list[str]): A list of tags to search for the command.

    Returns:
        str | None: The extracted command if found, otherwise None.
    """

    for tag in tags:
        match = re.search(r"cb:(.*)", tag)
        if match:
            cmd = match.group(1)
            return cmd
    return None


def init() -> Graph:
    """
    Initialize the graph.
    """

    log.info("Initialize Central Bureaucracy...")

    hh = init_hyperhound(SYSPROMPT_HYPER_HOUND)
    # ii = init_inkinspector(SYSPROMPT_INK_INSPECTOR_7000)

    g = Graph()
    g.add_node("arxiv", create_arxiv_note)
    g.add_node("hyperhound", hh)
    # g.add_node("inkinspector7000", ii)

    def route(q: dict):
        path = q["path"]
        c = cmd(tags(fp=path))

        match c:
            case "arxiv":
                return "arxiv"
            case "fetch":
                q["query"] = pathlib.Path(path).stem
                return "hyperhound"
            case "ocr":
                return "inkinspector7000"
            case "code":
                return "codeclerk"
            case _:
                return END

    g.add_conditional_edges(
        START,
        route,
        # {
        #     "arxiv": "arxiv",
        #     "fetch": "hyperhound",
        #     "ocr": "inkinspector7000",
        #     "code": "codeclerk",
        #     END: END,
        # },
    )

    g.add_edge("hyperhound", END)
    g.add_edge("arxiv", END)

    return g.compile()


def main() -> None:
    g = init()
    runio(g, PATH)
