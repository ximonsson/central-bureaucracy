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

    log.info(f"Connect to database [{db}]")
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

    return con


def index(db: duckdb.DuckDBPyConnection, dir: str):
    """Index the notes in the specified directory.

    Args:
        db (duckdb.DuckDBPyConnection): The DuckDB database connection.
        dir (str): The directory containing the markdown files to index.
    """

    log.info(f"Re-index databaase @ [{dir}]")

    # create macro for extracting backlinks

    db.sql(
        """CREATE OR REPLACE MACRO links(x) AS
        regexp_extract_all(x, '\[\[([\w-_/\.]+)(\|.+)?\]\]', 1)"""
    )

    db.sql(
        f"""CREATE OR REPLACE TABLE note AS
        SELECT
            filename,
            regexp_extract(filename, '{dir}(.*)\.md', 1) AS name,
            content,
            size,
            last_modified,
            frontmatter(content) AS frontmatter,
            links(content) AS links,
        FROM read_text('{dir}/**/*.md')
        """
    )

    db.sql("""
        CREATE OR REPLACE VIEW link AS
        SELECT name AS source, unnest(links) AS target FROM note
    """)


def fetch(db: duckdb.DuckDBPyConnection, start: str, end: str) -> list[str]:
    """Fetch the BFS traversal from start to end in the database.

    Args:
        db (duckdb.DuckDBPyConnection): The database connection.
        start (str): The starting node for the traversal.
        end (str): The ending node for the traversal.

    Returns:
        list[str]: The BFS traversal from start to end.
    """

    # TODO fix return type
    # think about what information is needed for the LLM later.

    # TODO only include notes that are tagged #note

    return db.sql(
        f"""
        WITH RECURSIVE bfs_traversal AS (
            -- Start with the root node;
            SELECT
                source,
                target,
                0 AS level,
                ARRAY[source, target] AS path
            FROM
                link
            WHERE
                source = '{start}'

            UNION ALL

            -- Recursive part to join the paths
            SELECT
                e.source,
                e.target,
                b.level + 1,
                b.path || e.target
            FROM
                link e
            JOIN
                bfs_traversal b ON e.source = b.target
            WHERE
                NOT e.target = ANY(b.path) -- Check to avoid cycles
        )

        SELECT
            source, target, level
        FROM
            bfs_traversal
        ORDER BY
            level, source, target;
        """
    ).arrow()
