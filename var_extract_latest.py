import ast
import re

HEX_PATTERN = re.compile(r"\b0x[0-9A-Fa-f]+\b")


class CryptoVarExtractor(ast.NodeTransformer):
    def __init__(self):
        self.next_var_id = 0

        # Instead of global mapping, we keep per-scope mapping
        self.scope_stack = []  # Each element: {"mapping":{}, "assigns":[]}

    def _new_scope(self):
        scope = {"mapping": {}, "assigns": []}
        self.scope_stack.append(scope)
        return scope

    def _end_scope(self):
        return self.scope_stack.pop()

    def _make_var_name(self):
        name = f"cond_{self.next_var_id}"
        self.next_var_id += 1
        return name

    def _replace_condition(self, node):
        """Return ast.Name referencing a variable for this condition."""
        scope = self.scope_stack[-1]

        if id(node) not in scope["mapping"]:
            var_name = self._make_var_name()
            scope["mapping"][id(node)] = var_name

            assign = ast.Assign(
                targets=[ast.Name(id=var_name, ctx=ast.Store())],
                value=node
            )
            ast.fix_missing_locations(assign)
            scope["assigns"].append(assign)

        return ast.Name(id=scope["mapping"][id(node)], ctx=ast.Load())

    def visit_FunctionDef(self, node):
        self._new_scope()

        self.generic_visit(node)

        scope = self._end_scope()

        node.body = scope["assigns"] + node.body

        return node

    def visit_Module(self, node):
        self._new_scope()

        self.generic_visit(node)

        scope = self._end_scope()

        node.body = scope["assigns"] + node.body

        return node

    def visit_If(self, node):
        self.generic_visit(node)
        node.test = self._replace_condition(node.test)
        return node

    def visit_Compare(self, node):
        return self._replace_condition(self.generic_visit(node))

    def visit_BoolOp(self, node):
        return self._replace_condition(self.generic_visit(node))

    def get_refactored_code(self, source_code):
        hex_matches = list(HEX_PATTERN.finditer(source_code))
        hex_map = {}
        for m in hex_matches:
            hx = m.group()
            dec = str(int(hx, 16))
            hex_map[dec] = hx

        try:
            tree = ast.parse(source_code)

            new_tree = self.visit(tree)
            result = ast.unparse(new_tree)

        except Exception as e:
            raise ValueError(f"Parse transform failed: {e}")

        for dec, hx in hex_map.items():
            result = result.replace(dec, hx)

        return result
if __name__ == "__main__":
    src = """ 
a = 1
b = 4 
c = 3
d = 2

def fun():
    if a > b and (a != c) or (d != b):
        print("condition check 2")

if (a>b) or ((a !=b) or (c < d)) or ((c > a) and (b > d)):
    print("condition check")
else:
    pass
"""

    extractor = CryptoVarExtractor()
    print(extractor.get_refactored_code(src))