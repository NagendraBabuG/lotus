import ast
import builtins


class idCollector(ast.NodeVisitor):
    def __init__(self):
        self.ids = set()
        self.func_ids = set()
        self.class_ids = set()
        self.import_ids = set()

    def visit_Import(self, node):
        for alias in node.names:
            if alias.asname:
                self.import_ids.add(alias.asname)
            else:
                self.import_ids.add(alias.name.split(".")[0])

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.asname:
                self.import_ids.add(alias.asname)
            else:
                self.import_ids.add(alias.name)

        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.class_ids.add(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.func_ids.add(node.name)

        for arg in node.args.args:
            if arg.arg != "self":
                self.ids.add(arg.arg)

        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if isinstance(node.target, ast.Name):
            self.ids.add(node.target.id)

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
    def __init__(self, ids, func_ids, class_ids, import_ids):
        self.var_mapper = {}

        self.func_ids = set(func_ids)
        self.class_ids = set(class_ids)
        self.import_ids = set(import_ids)

        self.var_count = 0
        self.func_count = 0
        self.class_count = 0

        self._assign(ids, "var")
        self._assign(func_ids, "func")
        self._assign(class_ids, "class")

    def _should_skip(self, name):
        if name.startswith("__") and name.endswith("__"):
            return True

        if name in {"self", "cls"}:
            return True

        if name in dir(builtins):
            return True

        if name in self.import_ids:
            return True

        return False

    def _assign(self, names, prefix):
        for name in sorted(names):

            if self._should_skip(name):
                continue

            if name not in self.var_mapper:

                if prefix == "var":
                    new_name = f"var_{self.var_count}"
                    self.var_count += 1

                elif prefix == "func":
                    new_name = f"func_{self.func_count}"
                    self.func_count += 1

                else:
                    new_name = f"class_{self.class_count}"
                    self.class_count += 1

                self.var_mapper[name] = new_name

    def visit_ClassDef(self, node):
        self.generic_visit(node)

        if (
            node.name in self.var_mapper
            and not self._should_skip(node.name)
        ):
            node.name = self.var_mapper[node.name]

        return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)

        # rename function name
        if (
            node.name in self.var_mapper
            and not self._should_skip(node.name)
        ):
            node.name = self.var_mapper[node.name]

        # rename function args
        for arg in node.args.args:
            if (
                arg.arg in self.var_mapper
                and not self._should_skip(arg.arg)
            ):
                arg.arg = self.var_mapper[arg.arg]

        return node

    def visit_Attribute(self, node):
        """
        Handle attribute renaming safely.

        Correct:
            self.value        -> self.var_0
            self.encrypt()    -> self.func_0()
            MyClass.value     -> class_0.var_0
            MyClass.encrypt() -> class_0.func_0()

        Do NOT rename:
            hashlib.sha256
            os.path.join
        """

        self.generic_visit(node)

        # skip imported module attributes
        if (
            isinstance(node.value, ast.Name)
            and node.value.id in self.import_ids
        ):
            return node

        # rename accessed attribute
        if (
            node.attr in self.var_mapper
            and not self._should_skip(node.attr)
        ):
            node.attr = self.var_mapper[node.attr]

        return node

    def visit_keyword(self, node):
        """
        Do NOT rename keyword argument names.

        Correct:
            encrypt(message=var_0)

        Wrong:
            encrypt(var_0=var_0)
        """

        # only visit keyword value
        node.value = self.visit(node.value)

        return node

    def visit_Name(self, node):
        if (
            node.id in self.var_mapper
            and not self._should_skip(node.id)
        ):
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
                collector.import_ids,
            )

            new_tree = replacer.visit(tree)

            ast.fix_missing_locations(new_tree)

            return ast.unparse(new_tree)

        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")