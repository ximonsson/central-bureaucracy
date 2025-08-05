import duckdb
import datetime
from .io import frontmatter
import io
import logging

log = logging.getLogger("central-bureaucracy-db")
log.setLevel(logging.DEBUG)


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
    except duckdb.InvalidInputException as e:
        log.debug(e)

    # create UDF to extract front matter
    #   here we only want tags and date it was created.

    def front(fp: str) -> dict | None:
        fm = frontmatter(f=io.StringIO(fp))

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


def index(db: duckdb.DuckDBPyConnection, dir: str):
    """Index the notes in the specified directory.

    Args:
        db (duckdb.DuckDBPyConnection): The DuckDB database connection.
        dir (str): The directory containing the markdown files to index.
    """

    db.sql(
        f"""CREATE OR REPLACE VIEW notes AS
        SELECT *, frontmatter(content) AS frontmatter, links(content) AS links FROM read_text('{dir}/**/*.md')
        """
    )


def fetch(db: duckdb.DuckDBPyConnection, start: str, end: str) -> list[str]:
    # TODO
    # fix this stolen code
    db.sql(
        """WITH RECURSIVE tag_hierarchy(id, source, path) AS (
            SELECT id, name, [name] AS path
            FROM tag
            WHERE subclassof IS NULL
        UNION ALL
            SELECT tag.id, tag.name, list_prepend(tag.name, tag_hierarchy.path)
            FROM tag, tag_hierarchy
            WHERE tag.subclassof = tag_hierarchy.id
        )
        SELECT path
        FROM tag_hierarchy
        WHERE source = 'Oasis';"""
    )
