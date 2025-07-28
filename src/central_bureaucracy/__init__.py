import dotenv
import os
import pathlib
from .db import connect  # noqa
from .io import run as runio, tags
import mlflow
import hyperhound
import inkinspector7000
import codeclerk
import logging
import arxiv
import re
import agents
import argparse
import asyncio

# setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("central-bureaucracy")
log.setLevel(logging.DEBUG)

# tracing
agents.set_tracing_disabled(True)
mlflow.openai.autolog()
mlflow.langchain.autolog()

dotenv.load_dotenv()

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

    return hyperhound.create_agent(HYPER_HOUND_MODEL, prompt, temp=0.1)


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
        try:
            with open(INK_INSPECTOR_7000_SYSPROMPT) as f:
                prompt = f.read()
        except FileNotFoundError:
            prompt = INK_INSPECTOR_7000_SYSPROMPT

    return inkinspector7000.agent(INK_INSPECTOR_7000_MODEL, prompt)


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
        try:
            with open(CODE_CLERK_SYSPROMPT) as f:
                prompt = f.read()
        except FileNotFoundError:
            prompt = CODE_CLERK_SYSPROMPT

    return codeclerk.agent(CODE_CLERK_MODEL, prompt)


def create_arxiv_note(path: str):
    """Create a note from an arXiv paper."""

    # filename should be the arxiv ID
    filename = pathlib.Path(path).stem
    log.info("Create arXiv note for: %s", filename)
    content = arxiv.create_note(filename)
    return content


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


async def fetch(agent, path: str) -> str:
    """
    Fetch information related to a file and compile a note for it.
    """

    filename = pathlib.Path(path).stem
    input = f"Search for information related to '{filename.replace('-', ' ')}' and compile a note for it."
    r = await agents.Runner().run(agent, input)

    # TODO
    # update the file with content

    return r.final_output


async def code(agent, path: str) -> str:
    r = await agents.Runner().run(agent, path)

    # TODO
    # Create new file with code snippet

    return r.final_output


async def ocr(agent, path: str) -> str:
    r = await agents.Runner().run(agent, path)

    # TODO
    # create new file with output

    return r.final_output


def init() -> callable:
    """
    Initialize the graph.
    """

    # TODO
    # Re-consider going back to a langgraph graph or not.

    log.info("Initialize Central Bureaucracy...")

    hh = init_hyperhound()
    ii = init_inkinspector()
    cc = init_codeclerk()

    async def handle(path: str) -> str:
        c = cmd(tags(fp=path))
        log.info(f"Got command '{c}' from {path}")

        match c:
            case "arxiv":
                return create_arxiv_note(path)

            case "fetch":
                return await fetch(hh, path)

            case "code":
                return await code(cc, path)

            case "ocr":
                return await ocr(ii, path)

            case _:
                raise ValueError(f"Unrecognized command '{c}'!")

    return handle


def main() -> None:
    cb = init()
    runio(cb, PATH)


def main_fetch():
    parser = argparse.ArgumentParser(description="Fetch info on a file.")
    parser.add_argument("filepath", type=str, help="Path to the file")
    args = parser.parse_args()

    filename = args.filepath
    hh = init_hyperhound()
    output = asyncio.run(fetch(hh, filename))
    print(output)
