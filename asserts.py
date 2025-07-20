import ast

class AddAssertions(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        param_names = [arg.arg for arg in node.args.args if arg.arg != 'self']

        if param_names:
            conditions = [
                ast.Compare(
                    left=ast.Name(id=name, ctx=ast.Load()),
                    ops=[ast.NotEq()],
                    comparators=[ast.Constant(value=None)]
                ) for name in param_names
            ]

            assert_stmt = ast.Assert(
                test=ast.BoolOp(op=ast.And(), values=conditions)
            )

            node.body.insert(0, assert_stmt)

        return node

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            tree = self.visit(tree)
            ast.fix_missing_locations(tree)
            return ast.unparse(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
