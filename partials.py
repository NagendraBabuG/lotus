import ast
from typing import Dict, List, Set


class PartialsRefactor(ast.NodeTransformer):

    def __init__(self):
        self.scope_stack: List[Dict[str, ast.Constant]] = [{}]
        self.updated_vars: Set[str] = set()

    def _collect_updates(self, node):
        for n in ast.walk(node):
            if isinstance(n, ast.AugAssign):
                if isinstance(n.target, ast.Name):
                    self.updated_vars.add(n.target.id)

    def _current_scope(self):
        return self.scope_stack[-1]

    def _is_const_assign(self, node):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                return target.id not in self.updated_vars
        return False

    def _process_block(self, body):

        new_body = []

        for stmt in body:
            
            if self._is_const_assign(stmt):

                name = stmt.targets[0].id
                self._current_scope()[name] = stmt.value

                continue

            stmt = self.visit(stmt)

            new_body.append(stmt)

        return new_body

    def visit_Module(self, node):

        self._collect_updates(node)

        node.body = self._process_block(node.body)

        return node

    def visit_FunctionDef(self, node):

        self.scope_stack.append(self._current_scope().copy())

        node.body = self._process_block(node.body)

        self.scope_stack.pop()

        return node

    def visit_If(self, node):

        self.scope_stack.append(self._current_scope().copy())
        node.body = self._process_block(node.body)
        self.scope_stack.pop()

        self.scope_stack.append(self._current_scope().copy())
        node.orelse = self._process_block(node.orelse)
        self.scope_stack.pop()

        return node

    def visit_Name(self, node):

        if isinstance(node.ctx, ast.Load):

            scope = self._current_scope()

            if node.id in scope:

                return ast.copy_location(scope[node.id], node)

        return node

    def get_refactored_code(self, source_code):

        tree = ast.parse(source_code)

        tree = self.visit(tree)

        ast.fix_missing_locations(tree)

        return ast.unparse(tree)


