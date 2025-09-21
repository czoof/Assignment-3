"""YouTube-like simple console app.

Features:
- Upload videos (metadata only)
- List videos
- View video details
- Delete videos
- Search by title or tags
- Persist videos to `videos.json`
- `--demo` mode to run a small scripted demo
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
    id: int
    title: str
    description: str
    uploader: str
    tags: List[str] = field(default_factory=list)
    uploaded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class VideoStore:
    def __init__(self, path: str = DB_FILE):
        self.path = path
        self.videos: List[Video] = []
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            self.videos = []
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.videos = [Video(**v) for v in data]
        except Exception:
            self.videos = []

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([asdict(v) for v in self.videos], f, indent=2)

    def next_id(self) -> int:
        return max((v.id for v in self.videos), default=0) + 1

    def add(self, title: str, description: str, uploader: str, tags: Optional[List[str]] = None) -> Video:
        vid = Video(id=self.next_id(), title=title, description=description, uploader=uploader, tags=tags or [])
        self.videos.append(vid)
        self._save()
        return vid

    def list(self) -> List[Video]:
        return list(self.videos)

    def get(self, video_id: int) -> Optional[Video]:
        for v in self.videos:
            if v.id == video_id:
                return v
        return None

    def delete(self, video_id: int) -> bool:
        before = len(self.videos)
        self.videos = [v for v in self.videos if v.id != video_id]
        changed = len(self.videos) != before
        if changed:
            self._save()
        return changed

    def search(self, query: str) -> List[Video]:
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
    if not args.title:
        print("Error: --title is required for upload")
        return 2
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    v = store.add(title=args.title, description=args.description, uploader=args.uploader, tags=tags)
    print(f"Uploaded video: id={v.id} title='{v.title}' uploader='{v.uploader}'")
    return 0


def cmd_list(store: VideoStore, args: argparse.Namespace):
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
