from pathlib import Path

DEFAULT_IGNORED = [".git/", "__pycache__/", ".DS_Store"]

def build_tree(path: Path, ignore_list=None, filter_list=None):
    """
    Builds a nested dict tree structure with filtering and ignore rules applied.
    """
    ignore_list = ignore_list or []
    filter_list = filter_list or []
    all_ignored = set(DEFAULT_IGNORED + ignore_list)

    def recurse(p: Path):
        # Ignore rules
        for pattern in all_ignored:
            if pattern.endswith("/"):
                if p.is_dir() and p.name == pattern[:-1]:
                    return None
            elif pattern.startswith('"') and pattern.endswith('"'):
                if p.suffix == pattern.strip('"'):
                    return None
            else:
                if p.is_file() and p.name == pattern:
                    return None

        # Filter substrings
        if filter_list and not any(f.lower() in p.name.lower() for f in filter_list):
            return None

        node = {"name": p.name, "path": str(p), "children": []}
        if p.is_dir():
            children = filter(None, (recurse(c) for c in sorted(p.iterdir())))
            node["children"] = list(children)
        return node

    return recurse(path)

def flatten_tree(node):
    """
    Returns a flat list of all nodes in pre-order traversal.
    Each element: (node_dict, depth)
    """
    result = []

    def dfs(n, depth=0):
        result.append((n, depth))
        for c in n.get("children", []):
            dfs(c, depth + 1)

    dfs(node)
    return result
