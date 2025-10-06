import ast
import re
import sys
import tokenize
import typing as _t
from ast import *  # noqa: F401,F403
from collections.abc import Iterable


class Comment(ast.AST):
    if sys.version_info >= (3, 10):
        __match_args__ = ("value", "inline")
    _attributes = ["lineno", "col_offset", "end_lineno", "end_col_offset"]
    value: str
    inline: bool
    _fields = (
        "value",
        "inline",
    )


_CONTAINER_ATTRS = ["body", "handlers", "orelse", "finalbody"]


def parse(source: _t.Union[str, bytes, ast.AST], *args, **kwargs) -> ast.AST:
    tree = ast.parse(source, *args, **kwargs)
    if isinstance(source, (str, bytes)):
        _enrich(source, tree)

    # Add parent pointers to all nodes
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node

    return tree


def _enrich(source: _t.Union[str, bytes], tree: ast.AST) -> None:
    if isinstance(source, bytes):
        source = source.decode()
    lines_iter = iter(source.splitlines(keepends=True))
    tokens = tokenize.generate_tokens(lambda: next(lines_iter))

    comment_nodes = []
    for t in tokens:
        if t.type != tokenize.COMMENT:
            continue
        lineno, col_offset = t.start
        end_lineno, end_col_offset = t.end
        c = Comment(
            value=t.string,
            inline=t.string != t.line.strip("\n").lstrip(" "),
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
        )
        comment_nodes.append(c)

    if not comment_nodes:
        return

    tree_intervals = _get_tree_intervals_and_update_ast_nodes(tree, source)
    for c_node in comment_nodes:
        c_lineno = c_node.lineno
        possible_intervals_for_c_node = [
            (x, y) for x, y in tree_intervals if x <= c_lineno <= y
        ]

        if possible_intervals_for_c_node:
            target_interval = tree_intervals[
                max(possible_intervals_for_c_node,
                    key=lambda item: (item[0], -item[1]))
            ]

            target_node = target_interval["node"]
            # intervals for every attribute from _CONTAINER_ATTRS for the target node
            sub_intervals = target_interval["intervals"]

            loc = -1
            for i, (low, high, _) in enumerate(sub_intervals):
                if low <= c_lineno <= high or c_lineno < low:
                    loc = i
                    break

            *_, target_attr = sub_intervals[loc]
        else:
            target_node = tree
            target_attr = "body"

        attr = getattr(target_node, target_attr)
        attr.append(c_node)
        attr.sort(key=lambda x: (x.end_lineno, isinstance(x, Comment)))

        # NOTE:
        # Due to some issues it's possible for comment nodes to go outside of their initial place
        # after the parse-unparse roundtip:
        #   before parse/unparse:
        #   ```
        #   # comment 0
        #   some_code  # comment 1
        #   ```
        #   after parse/unparse:
        #   ```
        #   # comment 0  # comment 1
        #   some_code
        #   ```
        # As temporary workaround I decided to correct inline attributes here so they don't
        # overlap with each other. This place should be revisited after solving following issues:
        # - https://github.com/t3rn0/ast-comments/issues/10
        # - https://github.com/t3rn0/ast-comments/issues/13
        for left, right in zip(attr[:-1], attr[1:]):
            if isinstance(left, Comment) and isinstance(right, Comment):
                right.inline = False


def _get_tree_intervals_and_update_ast_nodes(
    node: ast.AST, source: str
) -> _t.Dict[
    _t.Tuple[int, int], _t.Dict[str,
                                _t.Union[_t.List[_t.Tuple[int, int]], ast.AST]]
]:
    res = {}
    for node in ast.walk(node):
        attr_intervals = []
        for attr in _CONTAINER_ATTRS:
            if items := getattr(node, attr, None):
                if not isinstance(items, Iterable):
                    continue
                attr_intervals.append(
                    (*_extend_interval(_get_interval(items), source), attr)
                )
        if attr_intervals:
            # If the parent node hast lineno and end_lineno we extend them too, because there
            # could be comments at the end not covered by the intervals gathered in the attributes
            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                low, high = _extend_interval(
                    (node.lineno, node.end_lineno), source)
                node.lineno = low
                node.end_lineno = high
                # also update the end col offset corresponding to the new line
                node.end_col_offset = len(source.split("\n")[high - 1])
            else:
                low = (
                    min(node.lineno, min(attr_intervals)[0])
                    if hasattr(node, "lineno")
                    else min(attr_intervals)[0]
                )
                high = (
                    max(node.end_lineno, max(attr_intervals)[1])
                    if hasattr(node, "end_lineno")
                    else max(attr_intervals)[1]
                )

            res[(low, high)] = {"intervals": attr_intervals, "node": node}
    return res


# Try to move lower bound lower and upper bound higher while not going out of bounds concerning
# the current block. The method is based on indentation levels to find the correct upper and lower
# bounds of the interval looked at by checking where the indentation changes, and it marks the end
# of the interval
def _extend_interval(interval: _t.Tuple[int, int], code: str) -> _t.Tuple[int, int]:
    lines = code.split("\n")
    # Insert an empty line to correspond to the lineno values from ast nodes which start at 1
    # instead of 0
    lines.insert(0, "")

    low = interval[0]
    high = interval[1]
    skip_lower = False

    if low == high:
        # Covering inner blocks like the inside of an if block consisting of only one line
        start_indentation = _get_indentation_lvl(lines[low])
    else:
        # Covering cases of blocks starting at an outer term like 'if' and blocks with more than
        # one line
        lower_bound = _get_indentation_lvl(lines[low])
        start_indentation = max(
            lower_bound,
            _get_indentation_lvl(_get_first_line_not_comment(lines[low + 1:])),
        )
        if start_indentation != lower_bound:
            skip_lower = True

    while not skip_lower and low - 1 > 0:
        # The upper bound ignores comments which are not correctly aligned, due to the fact
        # that there must always be an ast node other than a comment one with a lower indentation
        # above
        if re.match(
            r"^ *#.*", lines[low - 1]
        ) or start_indentation <= _get_indentation_lvl(lines[low - 1]):
            low -= 1
        else:
            break

    while high + 1 < len(lines):
        if start_indentation <= _get_indentation_lvl(lines[high + 1]):
            high += 1
        else:
            break

    return low, high


# Searches for the first line not being a comment
# In each block there must be at least one, otherwise the code is not valid
def _get_first_line_not_comment(lines: _t.List[str]):
    for line in lines:
        if not line.strip():
            continue
        if not re.match(r"^ *#.*", line):
            return line
    return ""


def _get_indentation_lvl(line: str) -> int:
    line.replace("\t", "   ")
    res = re.findall(r"^ *", line)
    indentation = 0
    if len(res) > 0:
        indentation = len(res[0])
    return indentation


# get min and max line from a source tree
def _get_interval(items: _t.List[ast.AST]) -> _t.Tuple[int, int]:
    linenos, end_linenos = [], []
    for item in items:
        linenos.append(item.lineno)
        end_linenos.append(item.end_lineno)
    return min(linenos), max(end_linenos)


# `unparse` has been introduced in Python 3.9
if sys.version_info >= (3, 9):
    if sys.version_info < (3, 14):
        from ast import _Unparser as _AstUnparser
    else:
        from _ast_unparse import Unparser as _AstUnparser

    class _Unparser(_AstUnparser):
        def visit_Comment(self, node: Comment) -> None:
            if node.inline:
                self.write(f"  {node.value}")
            else:
                self.fill(node.value)

        def visit_If(self, node: ast.If) -> None:
            def _get_first_not_comment_idx(orelse: list[ast.stmt]) -> int:
                i = 0
                while i < len(orelse) and isinstance(orelse[i], Comment):
                    i += 1
                return i

            self.fill("if ")
            self.traverse(node.test)
            with self.block():
                self.traverse(node.body)
            # collapse nested ifs into equivalent elifs.
            while node.orelse:
                i = _get_first_not_comment_idx(node.orelse)
                if len(node.orelse[i:]) != 1 or not isinstance(node.orelse[i], ast.If):
                    break
                for c_node in node.orelse[:i]:
                    self.traverse(c_node)
                node = node.orelse[i]
                self.fill("elif ")
                self.traverse(node.test)
                with self.block():
                    self.traverse(node.body)
            # final else
            if node.orelse:
                self.fill("else")
                with self.block():
                    self.traverse(node.orelse)

    def unparse(ast_obj: ast.AST) -> str:
        return _Unparser().visit(ast_obj)


def pre_compile_fixer(tree: ast.AST) -> ast.AST:
    """
    The parse output from ast_comments cannot compile (see issue #23). This function can be
    run to fix the output so that it can compile.  This transformer strips out Comment nodes.
    """

    class RewriteComments(ast.NodeTransformer):
        def visit_Comment(self, node: ast.AST) -> ast.AST:
            return None

    return RewriteComments().visit(tree)
