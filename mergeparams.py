import ast, sys


class MergeCommonParams:
    def elems_not_merged(self, func_list1, func_list2, merged_funcs):
        com_elem = []
        for lst in merged_funcs:
            for elem in lst:
                com_elem.append(elem)
        for func1, func2 in zip(func_list1, func_list2):
            if func1 in com_elem or func2 in com_elem:
                return False
        return True
    
    def class_check(self, class_func_map, merged, class_ids):
        for class_id in class_ids:
            flag = 0

            if all(item in class_func_map[class_id] for item in merged):
                return True
        for item in merged:
            if item not in class_func_map[class_id]:
                flag = 1
            elif flag:
                return False
            
        return True

    def param_grouping(self, tree):
        self.outer_param_ls = []
        self.func_param_map = {}
        self.func_node_map = {}

        class_ids = []
        class_func_map = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                func_ls = []
                class_ids.append(node.name)
                for node2 in node.body:
                    if isinstance(node2, ast.FunctionDef):
                        func_ls.append(node2.name)
                    class_func_map[node.name] = func_ls

            elif isinstance(node, ast.FunctionDef):
                elem_ls = []
                for elem in node.args.args:
                    if elem.arg != 'self':
                        elem_ls.append(elem.arg)
                self.outer_param_ls.append(elem_ls)
                self.func_node_map[node.name] = node
                self.func_param_map[node.name] = elem_ls

        if len(self.outer_param_ls) < 2: return tree

        combined = {}
        pool = []
        unpool = []

        for i in range(len(self.outer_param_ls)):
            flag = 0
            for j in range(len(self.outer_param_ls)):
                if i != j and (set(self.outer_param_ls[i]) & set(self.outer_param_ls[j])):
                    flag = 1
                    if i not in pool:
                        pool.append(i)
                    if j not in pool:
                        pool.append(j)
                    current_coomon = list(set(self.outer_param_ls[i]) & set(self.outer_param_ls[j]))
            if not flag:
                unpool.append(i)
        unpooled_nodes = []
        index = -1

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                index += 1
                if index in unpool:
                    unpooled_nodes.append(node)
        val_based_rev = {k:v for k, v in sorted(combined.items(), key=lambda item : item[1][0], reverse=True)}

        func_to_merge = []

        for item in val_based_rev:
            first_func = int(item[4])
            second_func = int(item[5])

            if first_func in pool and second_func in pool:
                if first_func in pool:
                    pool.remove(first_func)
                if second_func in pool:
                    pool.remove(second_func)
                for item2 in val_based_rev:
                    if val_based_rev[item2][1] == val_based_rev[item][1]:
                        (val_based_rev[item2][2]).sort()

                        func_to_merge.append(val_based_rev[item2][2])
        updated_merge = []

        for i in range(len(func_to_merge)):
            for j in range(i + 1, len(func_to_merge)):

                if (set(func_to_merge[i])&set(func_to_merge[j])) and self.elems_not_merged(func_to_merge[i], func_to_merge[j], updated_merge):
                    merged = list(set(func_to_merge[i])|set(func_to_merge[j]))

                    if self.class_check(class_func_map, merged, class_ids):
                        merged.sort()
                        updated_merge.append(merged)
        dedup_merge = []

        for item in updated_merge:
            if item not in dedup_merge:
                dedup_merge.append(item)

        includ_funcs = []
        code_divs = []

        for ind in range(len(dedup_merge)):
            temp_node =ast.Module(
                body=[],
                type_ignores=[]
            )

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):     
                    if node.name in dedup_merge[ind]:
                        temp_node.body.append(node)
                        includ_funcs.append(node.name)
            code_divs.append(temp_node)


        for func_name in self.func_node_map:
            if func_name not in includ_funcs:
                code_divs.append(ast.Module(
                    body=[self.func_node_map[func_name]],
                    type_ignores=[]
                ))
        
        final_tree = ast.Module(
            body=[],
            type_ignores=[]
        )

        merge_index = -1

        for tree in code_divs:
            merge_index += 1

            param_ls = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    elem_ls = []
                    for elem in node.args.args:
                        if elem.arg != 'self':
                            elem_ls.append(elem.arg)
                    param_ls.append(elem_ls)

            
            if len(param_ls) < 2:
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        final_tree.body.append(node)
                continue
            common_param = param_ls[0]

            for ls in param_ls[1:]:
                common_param = list(set(common_param) & set(ls))

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    new_param_ls = []
                    current_args = [elem.arg for elem in node.args.args]

                    if common_param and (list(set(common_param)&set(current_args)) == common_param):
                        for idx, elem in enumerate(node.args.args):
                            if elem.arg not in common_param:
                                new_param_ls.append(elem.arg)

                        new_param_ls.append(f'mergedParam{merge_index}')



                        node.args.args = []

                        for elem in new_param_ls:
                            node.args.args.append(
                                ast.arg(arg=elem)
                            )
                elif isinstance(node, ast.Call):
                    for idx, elem in enumerate(node.args):
                        if isinstance(elem, ast.Name) and elem.id in common_param:
                            node.args[idx] = ast.Attribute(ast.Name(id=f'mergedParam{merge_index}', ctx=ast.Load()),
                                                            attr=elem.id,
                                                            ctx=ast.Load())
                        
            for inner_nodes in ast.walk(tree):
                if isinstance(inner_nodes, ast.FunctionDef):
                    final_tree.body.append(inner_nodes)

        fof_tree = ast.Module(
            body=[],
            type_ignores=[]
        )
        
        added_func = []
        for ids in class_func_map:
            class_node = ast.ClassDef(
                name='',
                bases=[],
                keywords=[],
                body=[],
                decorator_list=[],
                type_params=[]

            )

            for node in ast.walk(final_tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name in class_func_map[ids]:
                        class_node.name = ids
                        class_node.body.append(node)
                        added_func.append(node.name)

            
            fof_tree.body.append(class_node)

        for node in ast.walk(final_tree):
            if isinstance(node, ast.FunctionDef) and node.name not in added_func:
                fof_tree.body.append(node)


        return fof_tree
    

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            tree = self.param_grouping(tree)
            return ast.unparse(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
