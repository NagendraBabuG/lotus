import ast


class AddDefaultArgValue(ast.NodeTransformer):

    def __init__(self):
        self.func_par_map = {}

    def collect_mappings(self, tree):
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue

            literals = []
            seen = set()

            for sub in ast.walk(node):
                if isinstance(sub, ast.Constant):
                    if isinstance(sub.value, (str, int, float, bool)) or sub.value is None:
                        key = repr(sub.value)
                        if key not in seen:
                            literals.append(sub.value)
                            seen.add(key)

            param_list = [(f"vari_{i}", lit) for i, lit in enumerate(literals)]
            self.func_par_map[node] = param_list

        return tree

    def transform_functions(self, tree):

        class _Injector(ast.NodeTransformer):
            def __init__(self, param_map):
                self.param_map = param_map
                self.in_defaults = False

            def visit_FunctionDef(self, node):
                self.in_defaults = True
                node.args.defaults = [self.visit(d) for d in node.args.defaults]
                self.in_defaults = False
                node.body = [self.visit(n) for n in node.body]
                return node

            def visit_Constant(self, node):
                if self.in_defaults:
                    return node
                key = repr(node.value)
                if key in self.param_map:
                    return ast.copy_location(
                        ast.Name(id=self.param_map[key], ctx=ast.Load()),
                        node
                    )
                return node

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node in self.func_par_map:

                literal_to_param = {}

                for param, lit in self.func_par_map[node]:
                    literal_to_param[repr(lit)] = param
                    node.args.args.append(ast.arg(arg=param))
                    node.args.defaults.append(ast.Constant(value=lit))

                _Injector(literal_to_param).visit(node)

        return tree

    def get_refactored_code(self, source_code):
        tree = ast.parse(source_code)
        tree = self.collect_mappings(tree)
        tree = self.transform_functions(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)
