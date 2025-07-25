import ast


#takes constant value in functions and add it's as function parameter
#currently works on string constants only


class AddDefaultArgValue(ast.NodeTransformer):
    def __init__(self):
        self.func_par_map = {}  
        self.used_params = set()

    def collect_mappings(self, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                var_idx = 0
                param_list = []
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                        if stmt.value.args:
                            for arg in stmt.value.args:
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    param_name = f"var{var_idx}"
                                    param_list.append((param_name, arg.value))
                                    var_idx += 1
                        if stmt.value.keywords:
                            for kw in stmt.value.keywords:
                                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                                    param_list.append((kw.arg, kw.value.value))
                self.func_par_map[node.name] = param_list
        return tree

    def transform_functions(self, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in self.func_par_map:
                const_to_param = {}
                for param, value in self.func_par_map[node.name]:
                    node.args.args.append(ast.arg(arg=param))
                    node.args.defaults.append(ast.Constant(value=value))
                    const_to_param[value] = param

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
                                call_node.args.append(ast.Name(id=const_to_param[kw.value.value], ctx=ast.Load()))
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
