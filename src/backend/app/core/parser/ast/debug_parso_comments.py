import parso

code = """
def test():
    # Comment
    simple_call()
"""
module = parso.parse(code)
func = module.children[0]
suite = func.children[-1]
stmt = suite.children[1] # 0 is newline/indent?
# stmt is SimpleStmt?
print(f"Stmt type: {stmt.type}")
# Inside stmt, we might have the atom_expr directly or wrapped.
# simple_stmt -> small_stmt -> expr_stmt -> testlist_star_expr -> ...
# Let's find the atom_expr
def find_atom_expr(node):
    if node.type == 'atom_expr':
        return node
    if hasattr(node, 'children'):
        for child in node.children:
            res = find_atom_expr(child)
            if res: return res
    return None

atom_expr = find_atom_expr(stmt)
print(f"Atom Expr: {atom_expr}")

if atom_expr:
    parts = atom_expr.children[:-1]
    raw_code = "".join(c.get_code() for c in parts).strip()
    print(f"Raw Code: '{raw_code}'")
    
    # Try to get clean name
    clean_parts = []
    for c in parts:
        if hasattr(c, 'get_code'):
             # For the first part, we might want to strip prefix?
             # But get_code(include_prefix=False) is only for Leaf?
             if hasattr(c, 'get_code') and 'include_prefix' in c.get_code.__code__.co_varnames:
                 clean_parts.append(c.get_code(include_prefix=False))
             else:
                 # For non-leaf, we might need to recurse or just use get_code and strip?
                 # But internal whitespace is important for `a . b`.
                 clean_parts.append(c.get_code())
    
    print(f"Clean Code attempt: '{''.join(clean_parts)}'")
