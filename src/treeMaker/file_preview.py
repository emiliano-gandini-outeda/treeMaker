from pathlib import Path
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import TerminalFormatter


def get_syntax_highlighted_content(file_path: Path) -> str:
    """
    Returns syntax-highlighted content for a file using Pygments.
    Falls back to plain text if lexer detection fails.
    """
    try:
        lexer = get_lexer_for_filename(str(file_path))
    except Exception:
        lexer = TextLexer()
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception:
        text = f"Could not read file: {file_path}"
    return highlight(text, lexer, TerminalFormatter())
