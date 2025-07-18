import pyinotify
import os
import dotenv
import pathlib
from .db import connect
from .bots import init_hyperhound

__all__ = [connect]

dotenv.load_dotenv()
home = pathlib.Path.home()
DB = os.environ.get("CENTRAL_BUREAUCRACY_DB", home / "data/m47rix.duckdb")


class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        print("Creating:", event.pathname)

    def process_IN_DELETE(self, event):
        print("Removing:", event.pathname)


wm = pyinotify.WatchManager()  # Watch Manager
mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE  # watched events


def main2() -> None:
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    wm.add_watch("/tmp", mask, rec=True)
    notifier.loop()


def main() -> None:
    prompt_path = os.environ.get(
        "CENTRAL_BUREAUCRACY_HYPER_HOUND_SYSPROMPT", "prompts:/hyper-hound@champion"
    )
    hh = init_hyperhound(prompt_path)
    y = hh.invoke({"query": "futurama-central-bureaucracy"})
    print(y["messages"][-1].content)
