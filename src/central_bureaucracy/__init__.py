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

DB = os.environ.get("CB_DB", "data.duckdb")
PATH = os.environ.get("CB_PATH", "/tmp/cb")

# hyper hound

HYPER_HOUND_SYSPROMPT = os.environ.get(
    "CB_HYPER_HOUND_SYSPROMPT", "prompts:/hyper-hound@champion"
)
HYPER_HOUND_MODEL = os.environ.get("CB_HYPER_HOUND_MODEL", "hyper-hound")

# ink inspector 7000

INK_INSPECTOR_7000_SYSPROMPT = os.environ.get(
    "CB_INK_INSPECTOR_7000_SYSPROMPT", "prompts:/ink-inspector-7000@champion"
)
INK_INSPECTOR_7000_MODEL = os.environ.get(
    "CB_INK_INSPECTOR_7000_MODEL", "ink-inspector-7000"
)

# code clerk

CODE_CLERK_SYSPROMPT = os.environ.get(
    "CB_CODE_CLERK_SYSPROMPT", "prompts:/code-clerk@champion"
)
CODE_CLERK_MODEL = os.environ.get("CB_CODE_CLERK_MODEL", "code-clerk")


def init_hyperhound():
    """
    Initialize Hyper Hound.
    """

    log.info("Initialize Hyper Hound...")
    log.debug("Prompt: %s", HYPER_HOUND_SYSPROMPT)
    log.debug("Model ID: %s", HYPER_HOUND_MODEL)

    if HYPER_HOUND_SYSPROMPT.startswith("prompts:/"):
        prompt = mlflow.load_prompt(HYPER_HOUND_SYSPROMPT).template
    else:
        with open(HYPER_HOUND_SYSPROMPT) as f:
            prompt = f.read()

    return hyperhound.create_agent(HYPER_HOUND_MODEL, prompt)


def init_inkinspector():
    """
    Initialize Ink Inspector.
    """

    log.info("Initialize Ink Inspector 7000...")
    log.debug("Prompt: %s", INK_INSPECTOR_7000_SYSPROMPT)
    log.debug("Model ID: %s", INK_INSPECTOR_7000_MODEL)

    if INK_INSPECTOR_7000_SYSPROMPT.startswith("prompts:/"):
        prompt = mlflow.load_prompt(INK_INSPECTOR_7000_SYSPROMPT).template
    else:
        with open(INK_INSPECTOR_7000_SYSPROMPT) as f:
            prompt = f.read()

    return inkinspector7000.graph(INK_INSPECTOR_7000_MODEL, prompt)


def init_codeclerk():
    """
    Initialize Ink Inspector.

    Args:
        prompt_path str: path to the prompt file
    """

    log.info("Initialize Code Clerk...")
    log.debug("Prompt: %s", CODE_CLERK_SYSPROMPT)
    log.debug("Model ID: %s", CODE_CLERK_MODEL)

    if CODE_CLERK_SYSPROMPT.startswith("prompts:/"):
        prompt = mlflow.load_prompt(CODE_CLERK_SYSPROMPT).template
    else:
        with open(CODE_CLERK_SYSPROMPT) as f:
            prompt = f.read()

    return codeclerk.graph(CODE_CLERK_MODEL, prompt)


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

    hh = init_hyperhound()
    # ii = init_inkinspector()

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
