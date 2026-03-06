import ast


class HardcodedValues:

    SUPPORTED_TYPES = (str, int)

    def __init__(self):
        self.global_counter = 0
        self.function_counter = 0

    def _collect_literals(self, body):
        literals = set()

        for stmt in body:
            for sub in ast.walk(stmt):

                if isinstance(sub, ast.Call):

                    for arg in sub.args:
                        if isinstance(sub, ast.Call) and isinstance(arg, ast.Constant):
                            if isinstance(arg.value, self.SUPPORTED_TYPES):
                                literals.add(arg.value)

                    for kw in sub.keywords:
                        if isinstance(kw.value, ast.Constant):
                            if isinstance(kw.value.value, self.SUPPORTED_TYPES):
                                literals.add(kw.value.value)

        return literals

    class Replacer(ast.NodeTransformer):
        def __init__(self, mapping):
            self.mapping = mapping

        def visit_Call(self, node):
            self.generic_visit(node)

            new_args = []
            for arg in node.args:
                if isinstance(arg, ast.Constant) and arg.value in self.mapping:
                    new_args.append(
                        ast.Name(id=self.mapping[arg.value], ctx=ast.Load())
                    )
                else:
                    new_args.append(arg)

            node.args = new_args

            new_keywords = []
            for kw in node.keywords:
                if (
                    isinstance(kw.value, ast.Constant)
                    and kw.value.value in self.mapping
                ):
                    new_keywords.append(
                        ast.keyword(
                            arg=kw.arg,
                            value=ast.Name(
                                id=self.mapping[kw.value.value],
                                ctx=ast.Load(),
                            ),
                        )
                    )
                else:
                    new_keywords.append(kw)

            node.keywords = new_keywords
            return node

    def _inject_scope(self, node, is_global=False):

        literals = self._collect_literals(node.body)

        if not literals:
            return

        mapping = {}
        assigns = []

        for lit in sorted(literals, key=str):

            if is_global:
                name = f"g_var{self.global_counter}"
                self.global_counter += 1
            else:
                name = f"f_var{self.function_counter}"
                self.function_counter += 1

            mapping[lit] = name

            assign = ast.Assign(
                targets=[ast.Name(id=name, ctx=ast.Store())],
                value=ast.Constant(value=lit),
            )
            assigns.append(assign)

        replacer = self.Replacer(mapping)

        new_body = [replacer.visit(stmt) for stmt in node.body]

        node.body = assigns + new_body

    def refactor(self, tree):

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                self._inject_scope(node, is_global=False)

        self._inject_scope(tree, is_global=True)

        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):
        tree = ast.parse(source_code)
        return self.refactor(tree)
