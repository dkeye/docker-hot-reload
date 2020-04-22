import argparse
import os
from functools import partial

import pyinotify

# Exclude patterns
IGNORE = [
    ".*\.idea",
    ".*\.DS_Store",
    ".*\.git"
    ".*venv",
    ".*__pycache__",
    ".*litt\..*\.log"
]


class EventHandler(pyinotify.ProcessEvent):
    _on_change = None

    def __init__(self, on_change):
        super().__init__()
        self._on_change = on_change

    def _main(self, event):
        self._on_change(event.pathname)

    process_IN_CREATE = _main  # override events functions
    process_IN_MODIFY = _main


def sync_with_docker(local, remote, container, path):
    start_index = local.find(remote)
    remote_path = path[start_index:]

    print(f"Updating: {path=}")
    os.system(f"docker cp path {container}:{remote_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Auto-sync files from given root with docker container remote directory')
    parser.add_argument('root', help='Root directory to observe')
    parser.add_argument('-r', '--remote', dest='remote_root', required=True, help='Remote root to upload into')
    parser.add_argument('-c', '--container', dest='container_name', required=True,
                        help='Docker container name, use `docker ps` to find the your container name')
    args = parser.parse_args()
    root = args.root
    remote_root = args.remote_root
    container_name = args.container_name

    if remote_root not in root:
        print('Local root must observe the same directory as the remote')
        exit(1)

    print(f"{root=}, {remote_root=}, {container_name=}")

    kwargs = {'local': root,
              'remote_root': remote_root,
              'container_name': container_name}

    on_change = partial(sync_with_docker, **kwargs)
    handler = EventHandler(on_change)
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE
    excl = pyinotify.ExcludeFilter(IGNORE)
    wm.add_watch(root, mask, rec=True, exclude_filter=excl)
    notifier = pyinotify.Notifier(wm, handler)

    print("press ^C to stop")
    notifier.loop()


if __name__ == '__main__':
    main()
