import io
import yaml
import pyinotify


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


class EventHandler(pyinotify.ProcessEvent):
    """
    This class is an event handler for file system events. It processes events related to file creation and deletion.
    """

    def process_IN_CREATE(self, event):
        """
        This method is called when a file is created.
        """

        print("Creating:", event.pathname)

    def process_IN_DELETE(self, event):
        """
        This method is called when a file is deleted.
        """
        print("Removing:", event.pathname)


wm = pyinotify.WatchManager()  # Watch Manager
mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE  # watched events


def run(path: str) -> None:
    """
    This function sets up a file system watcher using pyinotify.
    It watches the specified path for changes and handles events accordingly.

    Args:
        path (str): The path to the directory or file to watch.

    Returns:
        None
    """

    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    wm.add_watch(path, mask, rec=True)
    notifier.loop()
