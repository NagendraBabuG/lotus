import ast


class idCollector(ast.NodeVisitor):

    def __init__(self):
        self.ids = set()
        self.func_ids = set()
        self.class_ids = set()

    def visit_ClassDef(self, node):
        self.class_ids.add(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.func_ids.add(node.name)

        for arg in node.args.args:
            if arg.arg != "self":
                self.ids.add(arg.arg)

        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:

            if isinstance(target, ast.Name):
                self.ids.add(target.id)

            elif isinstance(target, ast.Tuple):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.ids.add(elt.id)

            elif (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                self.ids.add(target.attr)

        self.generic_visit(node)


class idReplacer(ast.NodeTransformer):

    def __init__(self, ids, func_ids, class_ids):
        self.var_mapper = {}
        self._assign(ids, "var")
        self._assign(func_ids, "func")
        self._assign(class_ids, "class")

    def _should_skip(self, name):
        if name.startswith("__") and name.endswith("__"):
            return True
        if name in {"self", "cls"}:
            return True
        if name in dir(__builtins__):
            return True
        return False

    def _assign(self, names, prefix):
        for name in sorted(names):
            if self._should_skip(name):
                continue
            if name not in self.var_mapper:
                new_name = f"{prefix}_{len(self.var_mapper)}"
                self.var_mapper[name] = new_name

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        if node.name in self.var_mapper and not self._should_skip(node.name):
            node.name = self.var_mapper[node.name]
        return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)

        if node.name in self.var_mapper and not self._should_skip(node.name):
            node.name = self.var_mapper[node.name]

        used = set()
        for arg in node.args.args:
            if arg.arg in self.var_mapper:
                new_name = self.var_mapper[arg.arg]
                while new_name in used:
                    new_name += "_1"
                used.add(new_name)
                arg.arg = new_name

        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)

        if (
            isinstance(node.value, ast.Name)
            and node.value.id == "self"
            and node.attr in self.var_mapper
            and not self._should_skip(node.attr)
        ):
            node.attr = self.var_mapper[node.attr]

        return node

    def visit_keyword(self, node):
        self.generic_visit(node)

        if node.arg and not self._should_skip(node.arg):
            if node.arg in self.var_mapper:
                node.arg = self.var_mapper[node.arg]

        return node

    def visit_Name(self, node):
        if node.id in self.var_mapper and not self._should_skip(node.id):
            node.id = self.var_mapper[node.id]
        return node


class Id_gen:

    def get_refactored_code(self, code):
        try:
            tree = ast.parse(code)

            collector = idCollector()
            collector.visit(tree)

            replacer = idReplacer(
                collector.ids,
                collector.func_ids,
                collector.class_ids,
            )

            new_tree = replacer.visit(tree)
            ast.fix_missing_locations(new_tree)

            return ast.unparse(new_tree)

        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
        


