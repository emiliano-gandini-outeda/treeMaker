# TreeMaker 🌳

TreeMaker is a console-native TUI (Textual User Interface) tool to explore directories, select multiple folders, filter files/folders, generate tree views, and preview files with syntax highlighting—all from your terminal.

---

## Features

* Sidebar with viewport navigation (2 items above/below hovered node)
* Multi-folder selection
* Custom and default ignore rules
* Syntax-highlighted file preview
* Result screen with Copy / Save / Exit

---

## Installation

### Arch Linux / Manjaro

TreeMaker is not **yet** in the AUR, so install manually:

```bash
git clone https://github.com/emiliano-gandini-outeda/treemaker.git
cd treeMaker
pipx install /home/eclipse/Documents/GitHub/treeMaker
```

### Ubuntu / Debian-based

```bash
git clone https://github.com/emiliano-gandini-outeda/treemaker.git
cd treeMaker
python3 -m pip install --user .
```

Dependencies:

* Python 3.10+
* [Textual](https://pypi.org/project/textual/)
* [Pygments](https://pypi.org/project/pygments/)
* [Pyperclip](https://pypi.org/project/pyperclip/)

---

## Usage

Navigate to any folder in terminal:

```bash
treemaker
```

* Use arrow keys to move in the sidebar
* `[Select Folder]` to stage folder(s) for tree generation
* `[See File]` to preview files
* `/` to focus filter input and add ignore rules
* `[Toggle Ignored Defaults ⏵]` to include/exclude default ignored files/folders
* `[Generate Tree]` to see the final tree
* Copy/Save/Exit options available in the result screen

---

## Filter Rules

TreeMaker allows you to **ignore files and folders** when building a tree. You can combine **default ignores**, **custom ignores**, and **file-type filters**.

1. **Default Ignored**  
   - `node_modules/`  
   - `__pycache__/`  
   - `.git/`  
   - `.idea/`  
   - `.vscode/`  
   - `dist/`  
   - `build/`  
   - `.eggs/`  
   - `.venv/`  
   - `.DS_Store`  
   
   These can be toggled on/off via `[Toggle Ignored Defaults ⏵]`.

2. **Custom Ignore Input**

   * Add one rule per line in the input field.
   * Folder names must end with `/` (e.g., `node_modules/`).
   * File names are just the file (e.g., `example.txt`).
   * File types/extensions are wrapped in quotes (e.g., `"*.py"`).

3. **Staged Ignore List**

   * Shows **both default and custom ignores**.
   * Remove items via ❌ button; the tree updates live.

4. **Filter Behavior**

   * All ignored items are excluded from the sidebar and final tree.
   * Filtering applies recursively inside selected folders.

---

## License
This project is licensed under the GNU Affero General Public License version 3 (AGPLv3). View [LICENSE](LICENSE).
