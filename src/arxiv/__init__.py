import httpx
import xml.etree.ElementTree as ET
import yaml
import datetime


def metadata(arxiv_id: str) -> dict:
    """
    Fetch metadata for an article from the arXiv API.

    Args:
        arxiv_id (str): The arXiv ID of the article.

    Returns:
        dict: A dictionary containing the metadata of the article.
    """

    # make HTTP request

    url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    response = httpx.get(url)
    response.raise_for_status()
    xmldata = response.text

    # parse xml data to extract metadata
    # the API has support for multiple IDs but we will only send one so
    # we return results for the first result.

    root = ET.fromstring(xmldata)
    entry = root.find("{http://www.w3.org/2005/Atom}entry")

    metadata = {}
    metadata["title"] = entry.find("{http://www.w3.org/2005/Atom}title").text
    metadata["summary"] = entry.find("{http://www.w3.org/2005/Atom}summary").text
    metadata["published"] = entry.find("{http://www.w3.org/2005/Atom}published").text
    metadata["updated"] = entry.find("{http://www.w3.org/2005/Atom}updated").text
    metadata["authors"] = [
        author.find("{http://www.w3.org/2005/Atom}name").text
        for author in entry.findall("{http://www.w3.org/2005/Atom}author")
    ]
    metadata["categories"] = [
        category.attrib["term"]
        for category in entry.findall("{http://www.w3.org/2005/Atom}category")
    ]

    return metadata


# yaml.dump(metadata, sort_keys=False)


def note(metadata: dict) -> str:
    """
    Format metadata to markdown file in following format

    ```md
    ---
    all fields except title and summary in front matter
    ---
    # title

    > summary
    ```

    Args:

    Returns:
        str: Note content

    """

    title = metadata["title"]
    summary = metadata["summary"]

    summary = "\n> ".join(summary.split("\n"))

    del metadata["title"]
    del metadata["summary"]
    metadata["date"] = datetime.date.today()
    front_matter = yaml.dump(metadata, sort_keys=False)

    return f"""---
{front_matter}
---
# {title}

> {summary}
"""
