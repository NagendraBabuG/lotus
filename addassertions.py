import ast

class AddAssertions(ast.NodeTransformer):
    def add_assertions(self, tree):
        self.arg_list = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.args.args:
                    for argument in node.args.args:
                        self.arg_list.append(argument.arg)
        
        self.comp_stmt = []

        for arg in self.arg_list:
            stmt = ast.Compare(
                left = ast.Name(id=arg, ctx=ast.Load()),
                ops=[
                    ast.NotEq()
                ],
                comparators=[
                    ast.Constant(value=None)
                ]
            )
            self.comp_stmt.append(stmt)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(self.arg_list):
                    stmt = ast.Assert(
                        test=ast.BoolOp(
                            op=ast.And(),
                            values=[comp for comp in self.comp_stmt]
                        )
                    )
                    node.body.insert(0, stmt)
        return ast.unparse(tree)
    

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            return self.add_assertions(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
