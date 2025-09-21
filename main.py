"""YouTube-like simple console app.

This module provides two ways to interact with a small video metadata store:
- Command-line interface (CLI) for scripted usage
- Graphical user interface (GUI) built with Tkinter for interactive use

Videos are stored as JSON in `videos.json` (human readable). The GUI will launch
when the script is run without a positional command. The CLI preserves the
original functionality (upload/list/view/delete/search) and includes a `--demo`
mode that seeds example data and demonstrates operations.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except Exception:
    tk = None
    ttk = None
    messagebox = None
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Optional

DB_FILE = "videos.json"


@dataclass
class Video:
    """Simple dataclass representing video metadata.

    Fields:
    - id: integer identifier assigned by the store
    - title, description, uploader: basic metadata strings
    - tags: list of tag strings
    - uploaded_at: UTC ISO timestamp string set at creation
    """
    id: int
    title: str
    description: str
    uploader: str
    tags: List[str] = field(default_factory=list)
    uploaded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class VideoStore:
    """Persistent collection of Video objects stored in a JSON file.

    Responsibilities:
    - load existing videos from disk at startup
    - save changes to disk after add/delete
    - provide helpers to add/list/get/delete/search videos
    """
    def __init__(self, path: str = DB_FILE):
        # path to the JSON file used for persistence
        self.path = path
        # in-memory list of Video instances
        self.videos: List[Video] = []
        # load stored data (if any)
        self._load()

    def _load(self):
        # Load JSON array from file and instantiate Video objects.
        # If the file does not exist or is invalid, start with an empty list.
        if not os.path.exists(self.path):
            self.videos = []
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Create Video instances from stored dicts
            self.videos = [Video(**v) for v in data]
        except Exception:
            # Any error reading/parsing -> reset to empty store
            self.videos = []

    def _save(self):
        # Write current in-memory list to JSON file (pretty printed)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([asdict(v) for v in self.videos], f, indent=2)

    def next_id(self) -> int:
        # Determine next id (1-based incremental)
        return max((v.id for v in self.videos), default=0) + 1

    def add(self, title: str, description: str, uploader: str, tags: Optional[List[str]] = None) -> Video:
        # Create a new Video object, append to store, persist and return it
        vid = Video(id=self.next_id(), title=title, description=description, uploader=uploader, tags=tags or [])
        self.videos.append(vid)
        self._save()
        return vid

    def list(self) -> List[Video]:
        # Return a copy of the stored videos list
        return list(self.videos)

    def get(self, video_id: int) -> Optional[Video]:
        # Find and return a video by id
        for v in self.videos:
            if v.id == video_id:
                return v
        return None

    def delete(self, video_id: int) -> bool:
        # Remove a video by id. Return True if deletion happened.
        before = len(self.videos)
        self.videos = [v for v in self.videos if v.id != video_id]
        changed = len(self.videos) != before
        if changed:
            self._save()
        return changed

    def search(self, query: str) -> List[Video]:
        # Case-insensitive search across title, description and tags
        q = query.lower()
        results = [v for v in self.videos if q in v.title.lower() or q in v.description.lower() or any(q in t.lower() for t in v.tags)]
        return results


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="YouTube-like console simulator")
    p.add_argument("command", nargs="?", choices=["upload", "list", "view", "delete", "search"], help="action to perform")
    p.add_argument("--title", "-t", help="video title")
    p.add_argument("--description", "-d", default="", help="video description")
    p.add_argument("--uploader", "-u", default="anonymous", help="uploader name")
    p.add_argument("--tags", help="comma separated tags")
    p.add_argument("--id", type=int, help="video id for view/delete")
    p.add_argument("--query", help="search query")
    p.add_argument("--demo", action="store_true", help="run demo script")
    return p.parse_args(argv)


def cmd_upload(store: VideoStore, args: argparse.Namespace):
    # Validate and add a video from CLI args
    if not args.title:
        print("Error: --title is required for upload")
        return 2
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    v = store.add(title=args.title, description=args.description, uploader=args.uploader, tags=tags)
    print(f"Uploaded video: id={v.id} title='{v.title}' uploader='{v.uploader}'")
    return 0


def cmd_list(store: VideoStore, args: argparse.Namespace):
    # Print a simple listing of stored videos to stdout
    videos = store.list()
    if not videos:
        print("No videos uploaded yet.")
        return 0
    print(f"{len(videos)} video(s):")
    for v in videos:
        tags = ", ".join(v.tags) if v.tags else "-"
        print(f"[{v.id}] {v.title} (by {v.uploader}) tags: {tags} uploaded: {v.uploaded_at}")
    return 0


def cmd_view(store: VideoStore, args: argparse.Namespace):
    # Show JSON details for a specific video id
    if not args.id:
        print("Error: --id is required for view")
        return 2
    v = store.get(args.id)
    if not v:
        print(f"Video id={args.id} not found")
        return 1
    print(json.dumps(asdict(v), indent=2))
    return 0


def cmd_delete(store: VideoStore, args: argparse.Namespace):
    # Delete by id and print result code for CLI usage
    if not args.id:
        print("Error: --id is required for delete")
        return 2
    ok = store.delete(args.id)
    if ok:
        print(f"Deleted video id={args.id}")
        return 0
    else:
        print(f"Video id={args.id} not found")
        return 1


def cmd_search(store: VideoStore, args: argparse.Namespace):
    # Search and display a brief result list
    if not args.query:
        print("Error: --query is required for search")
        return 2
    results = store.search(args.query)
    if not results:
        print("No results")
        return 0
    print(f"{len(results)} result(s):")
    for v in results:
        print(f"[{v.id}] {v.title} by {v.uploader}")
    return 0


def run_demo(store: VideoStore):
    # Simple scripted demo used by the CLI --demo flag. It resets the store
    # (when run by the main flow) and uploads three example videos, then
    # exercises list/search/view/delete to demonstrate functionality.
    print("Running demo: uploading 3 videos, listing, searching, viewing, deleting")
    demos = [
        {"title": "My First Vlog", "description": "Hello world vlog", "uploader": "alice", "tags": "vlog,intro"},
        {"title": "Python Tutorial", "description": "Learn Python in 10 minutes", "uploader": "bob", "tags": "python,programming"},
        {"title": "Relaxing Music", "description": "Lo-fi beats", "uploader": "carol", "tags": "music,lofi"},
    ]
    for d in demos:
        args = argparse.Namespace(title=d["title"], description=d["description"], uploader=d["uploader"], tags=d["tags"])
        cmd_upload(store, args)
        time.sleep(0.1)
    print()
    cmd_list(store, argparse.Namespace())
    print()
    print("Search for 'python':")
    cmd_search(store, argparse.Namespace(query="python"))
    print()
    print("View id=2:")
    cmd_view(store, argparse.Namespace(id=2))
    print()
    print("Delete id=1:")
    cmd_delete(store, argparse.Namespace(id=1))
    print()
    cmd_list(store, argparse.Namespace())


def main(argv=None):
    args = parse_args(argv)
    store = VideoStore()

    if args.demo:
        # ensure fresh state for demo
        try:
            if os.path.exists(store.path):
                os.remove(store.path)
        except Exception:
            pass
        store = VideoStore()
        run_demo(store)
        return 0

    # If no command provided, launch GUI (if available)
    if not args.command:
        if tk is None:
            print("Tkinter is not available; please provide a command or install Tkinter.")
            return 2
        launch_gui(store)
        return 0

    cmd = args.command
    if cmd == "upload":
        return cmd_upload(store, args)
    if cmd == "list":
        return cmd_list(store, args)
    if cmd == "view":
        return cmd_view(store, args)
    if cmd == "delete":
        return cmd_delete(store, args)
    if cmd == "search":
        return cmd_search(store, args)
    print("Unknown command")
    return 2


def launch_gui(store: VideoStore):
    root = tk.Tk()
    root.title("YouTube-like Simulator")
    root.geometry("700x450")

    # Left: form to upload/search
    frm_left = ttk.Frame(root, padding=10)
    frm_left.pack(side=tk.LEFT, fill=tk.Y)

    ttk.Label(frm_left, text="Title").pack(anchor=tk.W)
    title_var = tk.StringVar()
    ttk.Entry(frm_left, textvariable=title_var, width=30).pack()

    ttk.Label(frm_left, text="Description").pack(anchor=tk.W, pady=(6, 0))
    desc_var = tk.StringVar()
    ttk.Entry(frm_left, textvariable=desc_var, width=30).pack()

    ttk.Label(frm_left, text="Uploader").pack(anchor=tk.W, pady=(6, 0))
    uploader_var = tk.StringVar(value="anonymous")
    ttk.Entry(frm_left, textvariable=uploader_var, width=30).pack()

    ttk.Label(frm_left, text="Tags (comma separated)").pack(anchor=tk.W, pady=(6, 0))
    tags_var = tk.StringVar()
    ttk.Entry(frm_left, textvariable=tags_var, width=30).pack()

    def on_upload():
        title = title_var.get().strip()
        if not title:
            messagebox.showwarning("Validation", "Title is required")
            return
        store.add(title=title, description=desc_var.get(), uploader=uploader_var.get(), tags=[t.strip() for t in tags_var.get().split(",") if t.strip()])
        refresh_list()
        messagebox.showinfo("Uploaded", f"Uploaded '{title}'")

    ttk.Button(frm_left, text="Upload", command=on_upload).pack(pady=(8, 8))

    ttk.Separator(frm_left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)

    ttk.Label(frm_left, text="Search").pack(anchor=tk.W)
    search_var = tk.StringVar()
    ttk.Entry(frm_left, textvariable=search_var, width=30).pack()

    def on_search():
        q = search_var.get().strip()
        if not q:
            refresh_list()
            return
        results = store.search(q)
        refresh_list(results)

    ttk.Button(frm_left, text="Search", command=on_search).pack(pady=(6, 0))

    # Right: list and actions
    frm_right = ttk.Frame(root, padding=10)
    frm_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    cols = ("id", "title", "uploader", "tags", "uploaded")
    tree = ttk.Treeview(frm_right, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c.title())
    tree.column("id", width=40, anchor=tk.CENTER)
    tree.column("title", width=220)
    tree.column("uploader", width=100)
    tree.column("tags", width=140)
    tree.column("uploaded", width=140)
    tree.pack(fill=tk.BOTH, expand=True)

    def refresh_list(items: Optional[List[Video]] = None):
        for i in tree.get_children():
            tree.delete(i)
        items = items if items is not None else store.list()
        for v in items:
            tree.insert("", tk.END, values=(v.id, v.title, v.uploader, ", ".join(v.tags) if v.tags else "-", v.uploaded_at))

    def on_view():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("View", "Select a video first")
            return
        item = tree.item(sel[0])
        vid = int(item["values"][0])
        v = store.get(vid)
        if not v:
            messagebox.showerror("Error", "Video not found")
            return
        messagebox.showinfo(f"Video {v.id}", json.dumps(asdict(v), indent=2))

    def on_delete():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "Select a video first")
            return
        item = tree.item(sel[0])
        vid = int(item["values"][0])
        if messagebox.askyesno("Confirm", f"Delete video id={vid}?"):
            store.delete(vid)
            refresh_list()

    btns = ttk.Frame(frm_right)
    btns.pack(fill=tk.X, pady=(6, 0))
    ttk.Button(btns, text="View", command=on_view).pack(side=tk.LEFT, padx=4)
    ttk.Button(btns, text="Delete", command=on_delete).pack(side=tk.LEFT, padx=4)
    ttk.Button(btns, text="Refresh", command=refresh_list).pack(side=tk.LEFT, padx=4)

    refresh_list()
    root.mainloop()


if __name__ == "__main__":
    raise SystemExit(main())
