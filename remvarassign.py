
#parameters passed should be not modified , a new varialbe will be delcraed so original values remains uncahnged

import ast

class ParameterRefactor(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        self.par_var_map = {}
        param_names = [arg.arg for arg in node.args.args]

        init_assignments = []

        for param in param_names:
            if param in ('self', 'cls'):
                continue
            copy_name = f"{param}_copy"
            self.par_var_map[param] = copy_name
            init_assignments.append(ast.Assign(
                targets=[ast.Name(id=copy_name, ctx=ast.Store())],
                value=ast.Name(id=param, ctx=ast.Load())
            ))

        new_body = init_assignments + [self.visit(stmt) for stmt in node.body]
        node.body = new_body
        return node

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Load, ast.Store, ast.Del)):
            if node.id in self.par_var_map:
                return ast.copy_location(
                    ast.Name(id=self.par_var_map[node.id], ctx=node.ctx),
                    node
                )
        return node

    def refactor_parameters(self, tree):
        return ast.fix_missing_locations(self.visit(tree))

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            modified_tree = self.refactor_parameters(tree)
            return ast.unparse(modified_tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
