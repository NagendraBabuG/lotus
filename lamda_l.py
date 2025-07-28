import ast

class LambdaRefactor(ast.NodeTransformer):
    def has_decorators(self, func_def: ast.FunctionDef) -> bool:
        return bool(func_def.decorator_list)

    def visit_Module(self, node):
        new_body = []
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and len(stmt.body) == 1 and not self.has_decorators(stmt):
                ret_stmt = stmt.body[0]
                if isinstance(ret_stmt, ast.Return) and ret_stmt.value is not None:
                    lambda_args = ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg(arg=arg.arg, annotation=None) for arg in stmt.args.args],
                        vararg=None if not stmt.args.vararg else ast.arg(arg=stmt.args.vararg.arg, annotation=None),
                        kwonlyargs=[],
                        kw_defaults=[],
                        kwarg=None if not stmt.args.kwarg else ast.arg(arg=stmt.args.kwarg.arg, annotation=None),
                        defaults=stmt.args.defaults
                    )
                    lambda_assign = ast.Assign(
                        targets=[ast.Name(id=stmt.name, ctx=ast.Store())],
                        value=ast.Lambda(
                            args=lambda_args,
                            body=ret_stmt.value
                        )
                    )
                    ast.fix_missing_locations(lambda_assign)
                    new_body.append(lambda_assign)
                    continue
            new_body.append(stmt)
        node.body = new_body
        return node

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            tree = self.visit(tree)
            ast.fix_missing_locations(tree)
            return ast.unparse(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")