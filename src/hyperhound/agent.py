import agents
import openai
import os
import httpx
import markdownify
import ddgs


@agents.function_tool
def wiki_search(q: str) -> str:
    """
    Query the Wikipedia API for a given query string.

    Args:
        q (str): The query string to search for.

    Returns:
        str: The search results from the Wikipedia API.
    """

    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": q,
    }

    response = httpx.get(url, params=params)
    content = response.json()

    def fmt(item: dict):
        t = item["title"]
        pid = item["pageid"]
        c = markdownify.markdownify(item["snippet"])

        return f"title: {t}\npageid: {pid}\n{c}"

    return "\n\n---\n".join(map(fmt, content["query"]["search"]))


@agents.function_tool
def wiki_page(id: int) -> str:
    """
    Get the content of a Wikipedia page by its page ID.

    Args:
        id (int): The page ID of the Wikipedia page.

    Returns:
        str: The content of the Wikipedia page.
    """

    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions|info|pageimages",
        "rvprop": "content",
        "pageids": id,
        "rvslots": "main",
        "inprop": "url",
        "rvsection": "0",
    }

    response = httpx.get(url, params=params)
    content = response.json()
    page = content["query"]["pages"][str(id)]
    title = page["title"]
    url = page["fullurl"]
    content = page["revisions"][0]["slots"]["main"]["*"]
    thumbnail = page["thumbnail"]["source"] if "thumbnail" in page else ""

    return f"# {title}\n\nurl: {url}\nthumbnail: {thumbnail}\n\n---\n{content}"


@agents.function_tool
def web_search(q: str) -> str:
    """
    Perform a web search using the DuckDuckGo API.

    Args:
        q (str): The query string to search for.

    Returns:
        str: The search results from the DuckDuckGo API.
    """

    res = ddgs.DDGS().text(q, max_results=5)

    return "\n\n---\n".join(
        [f"## [{item['title']}]({item['href']})\n\n{item['body']}" for item in res]
    )


@agents.function_tool
def web_page(url: str) -> str:
    """
    Get web page content converted to markdown format.

    Args:
        url (str): The URL of the web page.

    Returns:
        str: The content of the web page in markdown format.
    """

    response = httpx.get(url)
    return markdownify.markdownify(response.text)


def new(model: str, prompt: str, temp: float = 0.0) -> agents.Agent:
    """
    Create a new agent with the given model, prompt, and temperature.

    Args:
        model (str): The model to use for the agent.
        prompt (str): The prompt to use for the agent.
        temp (float, optional): The temperature to use for the agent. Defaults to 0.0.

    Returns:
        agents.Agent: The created agent.
    """

    m = model
    c = openai.AsyncOpenAI(base_url=os.environ["OPENAI_API_BASE"])
    m = agents.OpenAIChatCompletionsModel(openai_client=c, model=m)

    return agents.Agent(
        model=m,
        name="Hyper Hound",
        instructions=prompt,
        model_settings=agents.ModelSettings(temperature=temp),
        tools=[wiki_search, wiki_page, web_search, web_page],
    )
