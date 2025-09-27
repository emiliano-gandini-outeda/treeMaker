import json
from pathlib import Path
import pyperclip
from .tree_utils import build_tree
from .file_preview import get_syntax_highlighted_content
import subprocess


DEFAULT_IGNORED = [
    ".git/", "__pycache__/", ".DS_Store",
    "node_modules", ".idea", ".vscode",
    "dist", "build", ".eggs", ".venv"
]


class TreeMakerCLI:
    def __init__(self, root: Path):
        self.original_root = root.resolve()
        self.current_path = root.resolve()
        self.ignore_list = DEFAULT_IGNORED.copy()
        self.filter_list = []
        self.staging = []
        self.entries = []
        self.last_print = ""  # stores last printed tree

    # -------------------------
    # Tree rendering
    # -------------------------
    def show_tree(self):
        tree = build_tree(self.current_path, self.ignore_list, self.filter_list, depth=1)
        if not tree or not tree.get("children"):
            print("Nothing to display (maybe filters/ignores too strict).")
            self.entries = []
            return

        self.entries = tree.get("children", [])
        print(f"\nCurrent folder: {self.current_path}")
        for i, entry in enumerate(self.entries):
            # Check if it's a directory using Path instead of relying on children
            path_obj = Path(entry["path"])
            mark = "[DIR]" if path_obj.is_dir() else "[FILE]"
            print(f"  [{i}] {mark} {entry['name']}")

    def render_tree_text(self, node, prefix=""):
        """Recursively render ASCII tree."""
        lines = []
        if node:
            lines.append(prefix + node["name"])
            children = node.get("children", [])
            for i, c in enumerate(children):
                branch = "├── " if i < len(children) - 1 else "└── "
                lines += self.render_tree_text(c, prefix + branch)
        return lines

    def print_ascii_tree(self):
        if not self.staging:
            print("Nothing staged. Run `stage` first.")
            return

        from pathlib import Path
        import os

        staged_paths = [Path(node["path"]).resolve() for node in self.staging]

        # If only one item is staged, use it as root
        if len(staged_paths) == 1:
            common_root = staged_paths[0]
        else:
            common_root = Path(os.path.commonpath(staged_paths))

        self.original_root = common_root

        def build_full_node(path: Path):
            node = {"name": path.name, "path": str(path), "children": []}
            if path.is_dir():
                for child in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                    if any(str(child).endswith(pat.strip("/")) for pat in self.ignore_list):
                        continue
                    node["children"].append(build_full_node(child))
            return node

        virtual_root = {"name": common_root.name, "path": str(common_root), "children": []}

        for node in self.staging:
            node_path = Path(node["path"]).resolve()
            # Attach fully if single folder staged, or if it's a direct child
            if len(staged_paths) == 1 or node_path == common_root:
                virtual_root = build_full_node(node_path)
                break
            else:
                # multiple staged nodes: attach under common_root
                relative_parts = node_path.relative_to(common_root).parts
                current = virtual_root
                for i, part in enumerate(relative_parts):
                    found = next((c for c in current["children"] if c["name"] == part), None)
                    if found:
                        current = found
                    else:
                        full_node = build_full_node(node_path) if i == len(relative_parts) - 1 else {"name": part, "path": str(node_path), "children": []}
                        current["children"].append(full_node)
                        current = full_node

        # Recursive renderer
        def render(node, prefix="", is_last=True):
            lines = []
            branch = "└── " if is_last else "├── "
            mark = "/" if Path(node["path"]).is_dir() else ""
            if prefix:
                lines.append(prefix + branch + node["name"] + mark)
            else:
                lines.append(node["name"] + mark)

            children = node.get("children", [])
            for i, child in enumerate(children):
                is_last_child = i == len(children) - 1
                child_prefix = prefix + ("    " if is_last else "│   ")
                lines += render(child, child_prefix, is_last_child)
            return lines

        self.last_print = "\n".join(render(virtual_root))
        print("\nASCII Tree Output:\n")
        print(self.last_print)
        print("\nTip: Use `copy` to copy the tree to clipboard or `save` to write to tree_output.txt\n")


    def show_full_tree(self):
        """Show the entire current tree with ignores and filters applied."""
        tree = build_tree(self.current_path, self.ignore_list, self.filter_list)
        if not tree:
            print("Nothing to show (maybe filters/ignores too strict).")
            return
        output_lines = self.render_tree_text(tree)
        preview = "\n".join(output_lines)
        print("\nFull tree preview:\n")
        print(preview)

    # -------------------------
    # Utilities
    # -------------------------
    def parse_indices(self, arg_str: str, max_index: int):
        """Parse comma-separated indices into a list of ints."""
        indices = []
        for part in arg_str.split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part)
                if 0 <= idx < max_index:
                    indices.append(idx)
        return indices

    def preview_file(self, idx: int, editor="less", lines_preview=50):
        """
        Open a file from the current entries in a read-only terminal editor.
        - idx: index from ls command
        - editor: terminal editor, e.g., less, nano, nvim
        - lines_preview: if editor not available, fallback to print first N lines
        """
        if idx < 0 or idx >= len(self.entries):
            print("Invalid index for preview")
            return

        entry = self.entries[idx]
        path = Path(entry["path"])
        if not path.is_file():
            print("Selected entry is not a file")
            return

        try:
            # Try opening with the specified editor in read-only mode
            if editor == "nano":
                subprocess.run(["nano", "-v", str(path)])
            elif editor == "nvim":
                subprocess.run(["nvim", "-R", str(path)])
            else:  # default: less
                subprocess.run(["less", str(path)])
        except FileNotFoundError:
            # Fallback: print first lines to console
            print(f"Editor '{editor}' not found. Showing first {lines_preview} lines:\n")
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f):
                    if i >= lines_preview:
                        print("... (truncated)")
                        break
                    print(line.rstrip())
    # -------------------------
    # Main loop
    # -------------------------
    def loop(self):
        print(f"TreeMaker CLI started in {self.original_root}\n")
        try:
            while True:
                cmd = input("Command: ").strip().split(maxsplit=1)
                if not cmd:
                    continue
                action = cmd[0]
                args = cmd[1] if len(cmd) > 1 else ""

                if action == "ls":
                    self.show_tree()

                elif action == "cd":
                    if args == "..":
                        self.current_path = self.current_path.parent
                    elif args.isdigit():
                        idx = int(args)
                        if 0 <= idx < len(self.entries):
                            target = Path(self.entries[idx]["path"])
                            if target.is_dir():
                                self.current_path = target
                            else:
                                print("Not a directory")
                        else:
                            print("Invalid index")
                    else:
                        print("Usage: cd <number> or cd ..")

                elif action == "help":
                    print("\nTreeMakerCLI Commands:\n")
                    
                    print("Navigation / Viewing")
                    print("  ls                    : List contents of the current folder")
                    print("  cd <number>           : Enter a subdirectory by its index from ls")
                    print("  up                    : Go to parent directory")
                    print("  root                  : Return to the original root directory")
                    print("  show <number>         : Preview a file (small snippet or read-only editor)")
                    
                    print("\nFiltering / Ignoring")
                    print("  filter <word>         : Show only files/folders containing <word>")
                    print("  ignore <pattern>      : Ignore a folder, file, or file type")
                    print("                          Examples:")
                    print("                            myfolder/  -> ignore folder")
                    print("                            file.txt   -> ignore a file")
                    print("                            .log       -> ignore all files with .log extension")
                    
                    print("\nStaging / Selection")
                    print("  stage <number[,number,...]>   : Add items from ls to staging area")
                    print("  unstage <number[,number,...]> : Remove items from staging area")
                    print("  staged                        : List items in staging area")
                    
                    print("\nOutput / Export")
                    print("  print                : Show ASCII tree of staged items")
                    print("  copy                 : Copy last printed tree to clipboard")
                    print("  save                 : Save last printed tree to tree_output.txt")
                    print("  export <json|md|txt> : Export staged/current ls contents to chosen format")
                    
                    print("\nUtility / Exit")
                    print("  help                 : Show this help table")
                    print("  quit                 : Exit TreeMakerCLI\n")

                elif action == "up":
                    parent = self.current_path.parent
                    if parent.exists():
                        self.current_path = parent
                    else:
                        print("Already at filesystem root")

                elif action == "root":
                    self.current_path = self.original_root

                elif action == "ignore":
                    if args == "-s":
                        print("Current ignore list:")
                        for pattern in self.ignore_list:
                            print(f"  {pattern}")
                        continue
                    if not args:
                        print("Usage: ignore <pattern>")
                        continue
                    pattern = args.strip()
                    self.ignore_list.append(pattern)
                    print(f"Added ignore pattern: {pattern}")

                elif action == "unignore":
                    if not args:
                        print("Usage: unignore <pattern>")
                        continue
                    pattern = args.strip()
                    if pattern in self.ignore_list:
                        self.ignore_list.remove(pattern)
                        print(f"Removed ignore pattern: {pattern}")
                    else:
                        print("Pattern not found in ignore list")

                elif action == "filter":
                    if not args:
                        print("Usage: filter <word>")
                        continue
                    self.filter_list.append(args)
                    print(f"Added filter: {args}")

                elif action == "show":
                    if args.isdigit():
                        idx = int(args)
                        if idx < 0 or idx >= len(self.entries):
                            print("Invalid index for show")
                            continue
                        entry = self.entries[idx]
                        path = Path(entry["path"])
                        if path.is_dir():
                            print("Error: 'show' can only be used on files, not directories")
                        else:
                            self.preview_file(idx)
                    else:
                        print("Usage: show <number> (index from ls)")

                elif action == "stage":
                    if not args:
                        print("Usage: stage <number[,number,...]>")
                        continue
                    indices = self.parse_indices(args, len(self.entries))
                    if not indices:
                        print("Invalid indices")
                        continue
                    for idx in indices:
                        item = self.entries[idx]
                        if item not in self.staging:
                            self.staging.append(item)
                            print(f"Staged: {item['name']}")

                elif action == "unstage":
                    if not args:
                        print("Usage: unstage <number[,number,...]>")
                        continue
                    indices = self.parse_indices(args, len(self.staging))
                    if not indices:
                        print("Invalid indices")
                        continue
                    for idx in sorted(indices, reverse=True):
                        removed = self.staging.pop(idx)
                        print(f"Unstaged: {removed['name']}")

                elif action == "staged":
                    if not self.staging:
                        print("Staging area empty")
                    else:
                        print("\nStaging Area:")
                        for i, entry in enumerate(self.staging):
                            print(f"  [{i}] {entry['name']}")

                elif action == "print":
                    self.print_ascii_tree()

                elif action == "copy":
                    if not self.last_print:
                        print("Nothing to copy. Run `print` first.")
                    else:
                        pyperclip.copy(self.last_print)
                        print("Tree copied to clipboard")

                elif action == "save":
                    if not self.last_print:
                        print("Nothing to save. Run `print` first.")
                    else:
                        out_file = self.original_root / "tree_output.txt"
                        out_file.write_text(self.last_print)
                        print(f"Saved tree to {out_file}")

                elif action == "export":
                    if not args:
                        print("Usage: export <json|md|txt>")
                        continue
                    fmt = args.lower()
                    out_file = self.original_root / f"tree_output.{fmt}"
                    data = self.staging if self.staging else self.entries
                    if not data:
                        print("Nothing to export (stage or run ls first)")
                        continue
                    if fmt == "json":
                        out_file.write_text(json.dumps(data, indent=2))
                    elif fmt == "md":
                        lines = [f"- {e['name']}" for e in data]
                        out_file.write_text("\n".join(lines))
                    elif fmt == "txt":
                        lines = [e['name'] for e in data]
                        out_file.write_text("\n".join(lines))
                    else:
                        print("Invalid format")
                        continue
                    print(f"Exported to {out_file}")

                elif action == "quit":
                    print("Exiting TreeMaker CLI")
                    break

                else:
                    print("Unknown command")
     
        except KeyboardInterrupt:
            print("\nExiting TreeMaker CLI (Keyboard Interrupt)")

def main():
    root_input = input("Enter root directory (default=current): ").strip()
    root_path = Path(root_input) if root_input else Path.cwd()
    if not root_path.exists():
        print("Directory not found")
        return
    app = TreeMakerCLI(root_path)
    app.loop()


if __name__ == "__main__":
    main()
