import ast
from random import shuffle


class ShuffleFunctions(ast.NodeTransformer):

    def shuffle_functions(self, tree):
        module_node = None

        for node in ast.walk(tree):
            if isinstance(node, ast.Module):
                module_node = node
                break

        if not module_node:
            return tree

        body = module_node.body

        func_nodes = []
        other_nodes = []
        doc_map = {}

        for stmt in body:
            if isinstance(stmt, ast.FunctionDef):
                func_nodes.append(stmt)

            elif (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Attribute)
                and isinstance(stmt.targets[0].value, ast.Name)
                and stmt.targets[0].attr == "__doc__"
            ):
                func_name = stmt.targets[0].value.id
                doc_map.setdefault(func_name, []).append(stmt)

            else:
                other_nodes.append(stmt)

        if not func_nodes:
            return tree

        shuffle(func_nodes)

        new_body = []
        used_docs = set()

        for func in func_nodes:
            new_body.append(func)

            if func.name in doc_map:
                for doc_stmt in doc_map[func.name]:
                    new_body.append(doc_stmt)
                    used_docs.add(id(doc_stmt))

        for stmt in other_nodes:
            if id(stmt) not in used_docs:
                new_body.append(stmt)

        module_node.body = new_body
        return tree

    def reorder_functions(self, tree):
        tree = self.shuffle_functions(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            return self.reorder_functions(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
