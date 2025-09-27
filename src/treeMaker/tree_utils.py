from pathlib import Path

def build_tree(path: Path, ignore_list=None, filter_list=None, depth=None):
    """
    Builds a nested dict tree structure.
    Each node: {"name": str, "path": str, "children": [subnodes]}
    - depth: maximum recursion depth. None = unlimited.
    """
    ignore_list = ignore_list or []
    filter_list = filter_list or []

    def recurse(p: Path, current_depth=0):
        # Stop recursion if depth exceeded
        if depth is not None and current_depth > depth:
            return None

        # Ignore rules
        for pattern in ignore_list:
            if pattern.endswith("/") and p.is_dir() and p.name == pattern[:-1]:
                return None
            if pattern.startswith('"') and pattern.endswith('"') and p.suffix == pattern.strip('"'):
                return None
            if not pattern.endswith("/") and not pattern.startswith('"') and p.is_file() and p.name == pattern:
                return None

        # Filter substrings
        if filter_list and not any(f.lower() in p.name.lower() for f in filter_list):
            return None

        node = {"name": p.name, "path": str(p), "children": []}
        if p.is_dir():
            children = filter(None, (recurse(c, current_depth + 1) for c in sorted(p.iterdir())))
            node["children"] = list(children)
        return node

    return recurse(path)


def flatten_tree(node):
    """Return a flat list of all nodes in pre-order traversal: [(node, depth)]"""
    result = []

    def dfs(n, depth=0):
        result.append((n, depth))
        for c in n.get("children", []):
            dfs(c, depth + 1)

    dfs(node)
    return result
