import ast
import copy


class SplitTempVar:

    # -----------------------------
    # Helper: safe rename for Name
    # -----------------------------
    def safe_replace(self, node, replace_name):
        if isinstance(node, ast.Name) and node.id in replace_name:
            node.id = replace_name[node.id]

    # -----------------------------
    # Fix: condition handling
    # -----------------------------
    def test_condition_checker(self, node2, replace_name):
        test = node2.test

        for inner in ast.walk(test):
            if isinstance(inner, ast.Name) and inner.id in replace_name:
                inner.id = replace_name[inner.id]

        return node2, replace_name

    # -----------------------------
    # Replace IDs (normal flow)
    # -----------------------------
    def replace_id(self, node, idx, replace_name, target_list):

        # Replace usage (Load only)
        for node2 in ast.walk(node):
            if isinstance(node2, ast.Name) and isinstance(node2.ctx, ast.Load):
                if node2.id in replace_name:
                    node2.id = replace_name[node2.id]

        # Handle assignment targets
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):   # FIX: safe check
                    if target.id in target_list:
                        new_name = f"{target.id}{idx}"
                        replace_name[target.id] = new_name
                        target.id = new_name
                        idx += 1
                    else:
                        target_list.append(target.id)

        return node, idx, replace_name, target_list

    # -----------------------------
    # Replace IDs inside IF/ELSE
    # -----------------------------
    def replace_id2(self, node, idx, replace_name, branch_targets, global_targets):

        for inner in ast.walk(node):
            if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load):
                if inner.id in replace_name:
                    inner.id = replace_name[inner.id]

        flag = 0

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):   # FIX
                    if target.id in global_targets:
                        new_name = f"{target.id}{idx}"
                        replace_name[target.id] = new_name
                        target.id = new_name

                        if target.id not in branch_targets:
                            branch_targets.append(target.id)

                        idx += 1
                        flag = 1
                    else:
                        global_targets.append(target.id)

        return node, idx, replace_name, branch_targets, global_targets, flag

    # -----------------------------
    # WHILE loop handling
    # -----------------------------
    def while_idx_loop(self, node, idx, replace_name, target_list):

        node, replace_name = self.test_condition_checker(node, replace_name)

        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.While):
                node.body[i], idx, replace_name, target_list = self.while_idx_loop(
                    stmt, idx, replace_name, target_list
                )
            elif isinstance(stmt, ast.If):
                node.body[i], idx, replace_name, target_list = self.if_idx_loop(
                    stmt, idx, replace_name, target_list
                )
            else:
                node.body[i], idx, replace_name, target_list = self.replace_id(
                    stmt, idx, replace_name, target_list
                )

        return node, idx, replace_name, target_list

    # -----------------------------
    # IF / ELSE handling
    # -----------------------------
    def if_idx_loop(self, node, idx, replace_name, target_list):

        node, replace_name = self.test_condition_checker(node, replace_name)

        # ----- IF branch -----
        if_idx = idx
        replace_if = copy.deepcopy(replace_name)
        if_targets = []

        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.While):
                node.body[i], if_idx, replace_if, target_list = self.while_idx_loop(
                    stmt, if_idx, replace_if, target_list
                )

            node.body[i], if_idx, replace_if, if_targets, target_list, _ = self.replace_id2(
                stmt, if_idx, replace_if, if_targets, target_list
            )

        # ----- ELSE branch -----
        else_idx = idx
        replace_else = copy.deepcopy(replace_name)
        else_targets = []

        for i, stmt in enumerate(node.orelse):
            if isinstance(stmt, ast.If):
                node.orelse[i], else_idx, replace_else, target_list = self.if_idx_loop(
                    stmt, else_idx, replace_else, target_list
                )
            elif isinstance(stmt, ast.While):
                node.orelse[i], else_idx, replace_else, target_list = self.while_idx_loop(
                    stmt, else_idx, replace_else, target_list
                )
            else:
                node.orelse[i], else_idx, replace_else, else_targets, target_list, _ = self.replace_id2(
                    stmt, else_idx, replace_else, else_targets, target_list
                )

        # ----- Merge branches -----
        if if_targets and else_targets and if_targets != else_targets:

            node.body.append(
                ast.Assign(
                    targets=[ast.Name(id="duplicate_id", ctx=ast.Store())],
                    value=ast.Name(id=if_targets[-1], ctx=ast.Load()),
                )
            )

            node.orelse.append(
                ast.Assign(
                    targets=[ast.Name(id="duplicate_id", ctx=ast.Store())],
                    value=ast.Name(id=else_targets[-1], ctx=ast.Load()),
                )
            )

            ast.fix_missing_locations(node)

        # ----- Choose dominant branch -----
        if len(if_targets) > len(else_targets):
            replace_name = replace_if
            idx = if_idx
            target_list = if_targets
        else:
            replace_name = replace_else
            idx = else_idx
            target_list = else_targets

        # FIX: avoid empty list crash
        if target_list:
            replace_name[target_list[-1]] = "duplicate_id"

        return node, idx, replace_name, target_list

    # -----------------------------
    # Main API
    # -----------------------------
    def get_refactored_code(self, code):
        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):

                    idx = 0
                    target_list = []
                    replace_name = {}

                    for i, stmt in enumerate(node.body):
                        if isinstance(stmt, ast.If):
                            node.body[i], idx, replace_name, target_list = self.if_idx_loop(
                                stmt, idx, replace_name, target_list
                            )
                        elif isinstance(stmt, ast.While):
                            node.body[i], idx, replace_name, target_list = self.while_idx_loop(
                                stmt, idx, replace_name, target_list
                            )
                        else:
                            node.body[i], idx, replace_name, target_list = self.replace_id(
                                stmt, idx, replace_name, target_list
                            )

            return ast.unparse(tree)

        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
