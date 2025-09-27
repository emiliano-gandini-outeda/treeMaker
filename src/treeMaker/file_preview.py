from pathlib import Path
import subprocess
import shutil

def get_syntax_highlighted_content(path: Path, max_lines: int = 20) -> str:
    """
    Returns the first few lines of a file for preview purposes.
    """
    try:
        with open(path, "r") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append("... (truncated)")
                    break
                lines.append(line.rstrip("\n"))
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading file: {e}"


def open_in_editor(path: Path, editor: str = None):
    """
    Opens the file in a read-only terminal editor.
    Default editor order: nvim > nano > less
    """
    path = path.resolve()
    if not path.exists():
        print(f"❌ File {path} does not exist")
        return

    # Detect available editor if not specified
    if editor is None:
        for e in ("nvim", "nano", "less"):
            if shutil.which(e):
                editor = e
                break
        else:
            print("❌ No supported editor found (nvim/nano/less)")
            return

    # Construct read-only flags
    flags = []
    if editor == "nvim":
        flags = ["-R"]
    elif editor == "nano":
        flags = ["-v"]  # view mode
    elif editor == "less":
        flags = []  # less is read-only by default

    try:
        subprocess.run([editor, *flags, str(path)])
    except Exception as e:
        print(f"❌ Failed to open editor: {e}")
