import duckdb
import yaml
import datetime
import io


def frontmatter(f: io.TextIOBase | None = None, fp: str | None = None) -> dict | None:
    """
    Extracts the front matter from a file.

    Args:
        f (io.TextIOBase | None): The file object to read from.
        fp (str | None): The path to the file to read from.

    Returns:
        dict | None: The front matter as a dictionary, or None if no front matter is found.
    """

    def _frontmatter(f: io.TextIOBase) -> dict | None:
        # read first line
        line = f.readline()

        if line[:-1] != "---":
            return None  # there is no frontmatter

        data = [line]
        line = f.readline()

        while line[:-1] != "---":
            data.append(line)
            line = f.readline()

        try:
            return yaml.safe_load("".join(data))
        except yaml.YAMLError:
            return None

    if f:
        return _frontmatter(f)

    with open(fp) as f:
        return _frontmatter(f)


def connect(db: str) -> duckdb.DuckDBPyConnection:
    """
    Connects to the DuckDB database.

    Args:
        db (str): The path to the DuckDB database file.

    Returns:
        duckdb.DuckDBPyConnection: The connection object to the DuckDB database.
    """

    con = duckdb.connect(db)

    try:
        con.remove_function("frontmatter")
    except duckdb.InvalidInputException:
        pass

    # create UDF to extract front matter
    #   here we only want tags and date it was created.

    def front(fp: str) -> dict | None:
        fm = frontmatter(fp)

        # some files will not have

        if fm is None:
            return None

        tags = fm.get("tags", [])
        d = fm.get("date", None)

        # cleaning of the date

        if isinstance(d, int):
            # in some old notes i wrote the date as an integer
            d = datetime.date.fromisoformat(str(d))
        elif isinstance(d, str) and d.startswith("{{"):
            # this is probably from a template
            d = None

        return {"tags": tags, "date": d}

    con.create_function(
        "frontmatter",
        front,
        return_type="STRUCT(tags VARCHAR[], date TIMESTAMP)",
        null_handling="special",
    )

    # create macro for extracting backlinks

    con.sql(
        """CREATE OR REPLACE MACRO links(x) AS
        regexp_extract_all(x, '\[\[([\w-_/\.]+)(\|.+)?\]\]', 1)"""
    )

    return con
