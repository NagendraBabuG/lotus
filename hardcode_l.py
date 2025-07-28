import ast

class HardcodedValues(ast.NodeTransformer):
    def __init__(self):
        self.constant_values = []
        self.new_stmt = []
        self.con_var_map = {}
        self.var_exp_map = {}
        self.current_function = None  

    def node_injector(self, node):
        if not isinstance(node, (ast.FunctionDef, ast.Module)):
            return node

        if isinstance(node, ast.FunctionDef):
            self.current_function = node
            self.constant_values = []
            self.con_var_map = {}
            self.var_exp_map = {}

            for n in ast.walk(node):
                if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
                    if n.value.args:
                        for arg in n.value.args:
                            if isinstance(arg, ast.Constant):
                                self.constant_values.append(arg.value)
                    if n.value.keywords:
                        for kw in n.value.keywords:
                            if isinstance(kw.value, ast.Constant):
                                self.constant_values.append(kw.value.value)

            index = 0
            for con in self.constant_values:
                var_name = f"var{index}"
                stmt = ast.Assign(
                    targets=[ast.Name(id=var_name, ctx=ast.Store())],
                    value=ast.Constant(value=con)
                )
                self.con_var_map[con] = var_name
                self.var_exp_map[var_name] = stmt
                ast.fix_missing_locations(stmt)
                index += 1

            for n in ast.walk(node):
                if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
                    if n.value.args:
                        for idx, arg in enumerate(n.value.args):
                            if isinstance(arg, ast.Constant) and arg.value in self.con_var_map:
                                n.value.args[idx] = ast.Name(id=self.con_var_map[arg.value], ctx=ast.Load())
                                ast.fix_missing_locations(n.value)
                    if n.value.keywords:
                        for idx, kw in enumerate(n.value.keywords):
                            if isinstance(kw.value, ast.Constant) and kw.value.value in self.con_var_map:
                                n.value.keywords[idx] = ast.keyword(
                                    arg=kw.arg,
                                    value=ast.Name(id=self.con_var_map[kw.value.value], ctx=ast.Load())
                                )
                                ast.fix_missing_locations(n.value)

            for index, elem in enumerate(node.body):
                if isinstance(elem, ast.Assign) and isinstance(elem.value, ast.Call):
                    if elem.value.args:
                        for const in elem.value.args:
                            if isinstance(const, ast.Name) and const.id in self.con_var_map.values():
                                if self.var_exp_map[const.id] not in node.body:
                                    node.body.insert(index, self.var_exp_map[const.id])
                                    ast.fix_missing_locations(node.body[index])
                    if elem.value.keywords:
                        for kw in elem.value.keywords:
                            if isinstance(kw.value, ast.Name) and kw.value.id in self.con_var_map.values():
                                if self.var_exp_map[kw.value.id] not in node.body:
                                    node.body.insert(index, self.var_exp_map[kw.value.id])
                                    ast.fix_missing_locations(node.body[index])

        return node

    def assign_var_to_hardcoded_values(self, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.node_injector(node)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            return self.assign_var_to_hardcoded_values(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")