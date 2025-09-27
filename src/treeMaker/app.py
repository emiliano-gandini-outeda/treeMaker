from textual.app import App, ComposeResult
from textual.widgets import Tree, Input, Button, Footer, Static, ListView, ListItem
from textual.containers import Vertical, Horizontal
from textual.screen import Screen
from textual.scroll_view import ScrollView
from pathlib import Path
from .tree_utils import build_tree
from .file_preview import get_syntax_highlighted_content
import pyperclip

DEFAULT_IGNORED = [
    ".git/", "__pycache__/", ".DS_Store",
    "node_modules", ".idea", ".vscode",
    "dist", "build", ".eggs", ".venv"
]

class TreeMaker(App):
    CSS_PATH = None
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("/", "focus_filter", "Filter"),
        ("up", "move_up"),
        ("down", "move_down")
    ]

    def __init__(self, start_path="."):
        super().__init__()
        self.start_path = Path(start_path).resolve()
        self.staged_folders = []
        self.custom_ignored = []
        self.default_ignored_enabled = True
        self.default_ignored_staged = DEFAULT_IGNORED.copy() if self.default_ignored_enabled else []
        self.filter_list = []
        self.current_tree_root = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="sidebar_container"):
                yield Tree(str(self.start_path), id="sidebar_tree")
            with Vertical(id="right_panel"):
                yield Static("Hover Info", id="hover_info")
                yield Button("Select Folder", id="select_folder")
                with Vertical(id="filter_section"):
                    yield Button("Toggle Ignored Defaults ⏵", id="toggle_ignored")
                    yield Input(placeholder='Add ignore rule here', id="ignore_input")
                    yield ListView(id="staged_list")
                    yield Button("Generate Tree", id="generate_tree")
        yield Footer()

    def on_mount(self):
        self.load_sidebar()

    # -------------------------
    # Sidebar / Tree Management
    # -------------------------
    def load_sidebar(self):
        all_ignores = self.custom_ignored + self.default_ignored_staged
        self.current_tree_root = build_tree(self.start_path, ignore_list=all_ignores, filter_list=self.filter_list)

        tree_widget: Tree = self.query_one("#sidebar_tree", Tree)
        tree_widget.root.remove_children()

        if self.current_tree_root:
            self.populate_tree(tree_widget.root, self.current_tree_root)

        tree_widget.root.expand()
        self.update_hover_info()

    def populate_tree(self, tree_node, data_node):
        """
        Recursively populate the Textual Tree widget:
        - Only directories get children and arrows
        - Files are leaves
        """
        if not data_node:
            return
        for child in data_node.get("children", []):
            path_obj = Path(child["path"])
            is_dir = path_obj.is_dir()
            label = f"{child['name']}/" if is_dir else child['name']
            new_node = tree_node.add(label, data=child)
            if is_dir:
                self.populate_tree(new_node, child)

    def update_hover_info(self):
        tree_widget: Tree = self.query_one("#sidebar_tree", Tree)
        node_data = tree_widget.cursor_node.data if tree_widget.cursor_node else self.current_tree_root
        if node_data:
            info = (
                f"Name: {node_data['name']}\n"
                f"Path: {node_data['path']}\n"
                f"Children: {len(node_data.get('children', []))}"
            )
            self.query_one("#hover_info", Static).update(info)

    # -------------------------
    # Ignore Management
    # -------------------------
    async def on_input_submitted(self, event: Input.Submitted):
        text = event.value.strip()
        if text and text not in self.custom_ignored:
            self.custom_ignored.append(text)
            self.load_sidebar()
        event.input.value = ""

    # -------------------------
    # Button Actions
    # -------------------------
    async def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        tree_widget: Tree = self.query_one("#sidebar_tree", Tree)
        node = tree_widget.cursor_node.data if tree_widget.cursor_node else None

        if btn_id == "select_folder" and node and Path(node["path"]).is_dir():
            if node["path"] not in self.staged_folders:
                self.staged_folders.append(node["path"])
                self.update_staged_list()
        elif btn_id == "generate_tree":
            await self.show_result_screen()
        elif btn_id == "toggle_ignored":
            self.default_ignored_enabled = not self.default_ignored_enabled
            self.default_ignored_staged = DEFAULT_IGNORED.copy() if self.default_ignored_enabled else []
            self.load_sidebar()

    def update_staged_list(self):
        list_widget: ListView = self.query_one("#staged_list", ListView)
        list_widget.clear()
        for folder in self.staged_folders:
            list_widget.append(ListItem(Static(folder)))

    # -------------------------
    # File Preview
    # -------------------------
    async def show_file_preview(self, file_path):
        content = get_syntax_highlighted_content(Path(file_path))

        class PreviewScreen(Screen):
            def compose(inner_self):
                yield ScrollView(Static(content))
                yield Button("Go Back", id="go_back")

            async def on_button_pressed(inner_self, event: Button.Pressed):
                if event.button.id == "go_back":
                    await inner_self.app.pop_screen()

        await self.push_screen(PreviewScreen())

    # -------------------------
    # Result Screen
    # -------------------------
    async def show_result_screen(self):
        content_lines = []
        for folder in self.staged_folders:
            tree = build_tree(Path(folder), ignore_list=self.custom_ignored + self.default_ignored_staged, filter_list=self.filter_list)
            if tree:
                content_lines.extend(self.render_tree_text(tree))
        content = "\n".join(content_lines)

        class ResultScreen(Screen):
            def compose(inner_self):
                yield ScrollView(Static(content))
                with Horizontal():
                    yield Button("Copy", id="copy")
                    yield Button("Save", id="save")
                    yield Button("Exit", id="exit_result")

            async def on_button_pressed(inner_self, event: Button.Pressed):
                if event.button.id == "copy":
                    pyperclip.copy(content)
                elif event.button.id == "save":
                    with open("tree_output.txt", "w") as f:
                        f.write(content)
                elif event.button.id == "exit_result":
                    await inner_self.app.pop_screen()
                    inner_self.app.staged_folders.clear()
                    inner_self.app.update_staged_list()
                    inner_self.app.load_sidebar()

        await self.push_screen(ResultScreen())

    def render_tree_text(self, node, prefix=""):
        lines = []
        if node:
            lines.append(prefix + node["name"])
            for i, c in enumerate(node.get("children", [])):
                branch = "├── " if i < len(node["children"]) - 1 else "└── "
                lines.extend(self.render_tree_text(c, prefix + branch))
        return lines

    # -------------------------
    # Key Actions
    # -------------------------
    def action_focus_filter(self):
        self.query_one("#ignore_input", Input).focus()

    def action_move_up(self):
        tree_widget: Tree = self.query_one("#sidebar_tree", Tree)
        tree_widget.cursor_up()
        self.update_hover_info()

    def action_move_down(self):
        tree_widget: Tree = self.query_one("#sidebar_tree", Tree)
        tree_widget.cursor_down()
        self.update_hover_info()


if __name__ == "__main__":
    print("Launching TreeMaker...")
    TreeMaker().run()
