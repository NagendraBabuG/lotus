import ast

#add exception codes as return 0/1

class ExceptionRefactor(ast.NodeTransformer):
    def __init__(self):
        self.current_function = None

    def visit_FunctionDef(self, node):
        self.current_function = node
        self.generic_visit(node)
        self.current_function = None
        return node

    def visit_Try(self, node):
        if self.current_function is None:
            return node  

        self.generic_visit(node)

        if not any(isinstance(stmt, ast.Return) for stmt in node.body):
            node.body.append(ast.Return(value=ast.Constant(value=1)))

        for handler in node.handlers:
            if isinstance(handler, ast.ExceptHandler):
                for idx, stmt in enumerate(handler.body):
                    if isinstance(stmt, ast.Raise) or (
                        isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant)
                    ):
                        handler.body[idx] = ast.Return(value=ast.Constant(value=0))
                if not any(isinstance(stmt, ast.Return) for stmt in handler.body):
                    handler.body.append(ast.Return(value=ast.Constant(value=0)))

        return node

    def visit_If(self, node):
        if self.current_function is None:
            return node  

        self.generic_visit(node)

        for idx, stmt in enumerate(node.body):
            if isinstance(stmt, ast.Raise):
                node.body[idx] = ast.Return(value=ast.Constant(value=1))
            elif isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant):
                if isinstance(stmt.value.value, int):
                    node.body[idx] = ast.Raise(
                        exc=ast.Call(
                            func=ast.Name(id='Exception', ctx=ast.Load()),
                            args=[ast.Constant(value="Operation Failed")],
                            keywords=[]
                        )
                    )

        for idx, stmt in enumerate(node.orelse):
            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant):
                if isinstance(stmt.value.value, int):
                    node.orelse[idx] = ast.Raise(
                        exc=ast.Call(
                            func=ast.Name(id='Exception', ctx=ast.Load()),
                            args=[ast.Constant(value="Operation Failed")],
                            keywords=[]
                        )
                    )
            elif isinstance(stmt, ast.Raise):
                node.orelse[idx] = ast.Return(value=ast.Constant(value=0))

        return node

    def refactor_exceptions(self, tree):
        self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            return self.refactor_exceptions(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
