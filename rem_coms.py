import ast
import re
import token
import tokenize
from io import BytesIO

HEX_PATTERN = re.compile(r"\b0x[0-9A-Fa-f]+\b")

class DocstringRemover(ast.NodeTransformer):
    def visit_Module(self, node):
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            node.body.pop(0)
        self.generic_visit(node)
        return node
        
    def visit_FunctionDef(self, node):
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            node.body.pop(0)
        self.generic_visit(node)
        return node
        
    def visit_ClassDef(self, node):
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            node.body.pop(0)
        self.generic_visit(node)
        return node

def get_refactored_code(source_code: str) -> str:
    try:
        tree = ast.parse(source_code)
        transformer = DocstringRemover()
        modified_tree = transformer.visit(tree)
        result = ast.unparse(modified_tree)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in source code: {e}")

    replacements = {}
    for match in HEX_PATTERN.finditer(source_code):
        hx = match.group(0)
        dec = str(int(hx, 16))
        if dec not in replacements:
            replacements[dec] = hx

    for dec, hx in sorted(replacements.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(r'\b' + re.escape(dec) + r'\b')
        result = pattern.sub(hx, result)

    return result

