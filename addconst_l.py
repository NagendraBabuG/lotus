import ast

class AddDefaultArgValue(ast.NodeTransformer):
    def __init__(self):
        self.func_par_map = {}
        self.used_params = set()

    def collect_mappings(self, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.used_params.clear()
                const_to_param = {}
                param_list = []
                var_idx = 0
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                        if stmt.value.args:
                            for arg in stmt.value.args:
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    value = arg.value
                                    if value not in const_to_param:
                                        param_name = f"var{var_idx}"
                                        while param_name in self.used_params:
                                            var_idx += 1
                                            param_name = f"var{var_idx}"
                                        const_to_param[value] = param_name
                                        param_list.append((param_name, value))
                                        self.used_params.add(param_name)
                                        var_idx += 1
                        if stmt.value.keywords:
                            for kw in stmt.value.keywords:
                                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                                    value = kw.value.value
                                    if value not in const_to_param:
                                        param_name = kw.arg
                                        if param_name in self.used_params:
                                            param_name = f"var{var_idx}"
                                            while param_name in self.used_params:
                                                var_idx += 1
                                                param_name = f"var{var_idx}"
                                        const_to_param[value] = param_name
                                        param_list.append((param_name, value))
                                        self.used_params.add(param_name)
                                        var_idx += 1
                self.func_par_map[node.name] = param_list
        return tree

    def transform_functions(self, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in self.func_par_map:
                const_to_param = {value: param for param, value in self.func_par_map[node.name]}
                for param, value in self.func_par_map[node.name]:
                    node.args.args.append(ast.arg(arg=param))
                    node.args.defaults.append(ast.Constant(value=value))
                class ReplaceConstantsInCalls(ast.NodeTransformer):
                    def visit_Call(self, call_node):
                        new_args = []
                        for arg in call_node.args:
                            if isinstance(arg, ast.Constant) and arg.value in const_to_param:
                                new_args.append(ast.Name(id=const_to_param[arg.value], ctx=ast.Load()))
                            else:
                                new_args.append(arg)
                        call_node.args = new_args
                        new_keywords = []
                        for kw in call_node.keywords:
                            if isinstance(kw.value, ast.Constant) and kw.value.value in const_to_param:
                                new_args.append(ast.Name(id=const_to_param[kw.value.value], ctx=ast.Load()))
                            else:
                                new_keywords.append(kw)
                        call_node.keywords = new_keywords
                        return call_node
                ReplaceConstantsInCalls().visit(node)
        return tree

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            tree = self.collect_mappings(tree)
            tree = self.transform_functions(tree)
            ast.fix_missing_locations(tree)
            return ast.unparse(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")