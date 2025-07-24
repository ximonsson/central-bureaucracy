import io
import yaml
import pyinotify
import logging

log = logging.getLogger("central-bureaucracy-io")
log.setLevel(logging.INFO)


def frontmatter(f: io.TextIOBase | None = None, fp: str | None = None) -> dict | None:
    """
    Extracts the front matter from a file.

    If a file object `f` is passed to the function it has precendence over the `fp` variable.
    If neither is passed a `ValueError` exception is raised.

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

    if f is None and fp is None:
        raise ValueError("Either f or fp must be provided")

    if f:
        return _frontmatter(f)

    with open(fp) as f:
        return _frontmatter(f)


def tags(f: io.TextIOBase | None = None, fp: str | None = None) -> list[str] | None:
    """
    Extracts the tags from the front matter of a file.

    Args:
        f (io.TextIOBase | None): The file object to read from.
        fp (str | None): The path to the file to read from.

    Returns:
        list[str] | None: The tags as a list of strings, or None if no tags are found.
    """

    return frontmatter(f=f, fp=fp)["tags"]


class EventHandler(pyinotify.ProcessEvent):
    """
    This class is an event handler for file system events. It processes events related to file creation and deletion.
    """

    def __init__(self, callback: callable):
        """
        Initialize the EventHandler with a callback.

        Args:
            callback (callable): The callback function to be called when an event is processed.
        """

        self.callback = callback

    def process_IN_CREATE(self, event):
        """
        This method is called when a file is created.
        """

        log.info("Creating:", event.pathname)
        self.callback(event.pathname)

    def process_IN_DELETE(self, event):
        """
        This method is called when a file is deleted.
        """

        log.info("Removing:", event.pathname)

    def process_IN_MODIFY(self, event):
        """
        This method is called when a file is modified.
        """

        log.info("Modifying:", event.pathname)
        self.callback(event.pathname)


wm = pyinotify.WatchManager()  # Watch Manager
mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MODIFY  # watched events


def run(callback: callable, path: str) -> None:
    """
    This function sets up a file system watcher and starts a loop to monitor for events.
    This function is blocking.

    Args:
        callback (callable): The callback function to be called when an event is processed.
        path (str): The path to the directory to watch.

    Returns:
        None
    """

    handler = EventHandler(callback)
    notifier = pyinotify.Notifier(wm, handler)
    wm.add_watch(path, mask, rec=True)
    notifier.loop()
