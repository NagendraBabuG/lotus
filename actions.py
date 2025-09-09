def return_empty_list(tree):
    return []

def return_tree(tree):
    return tree

def remove_publickey(tree):
   
    import libcst as cst

    class RemovePublicKey(cst.CSTTransformer):
        def leave_Assign(self, original_node, updated_node):
            if isinstance(updated_node.value, cst.Call):
                if isinstance(updated_node.value.func, cst.Attribute) and updated_node.value.func.attr.value == "publickey":
                    return cst.RemoveFromParent()
            return updated_node

    transformer = RemovePublicKey()
    tree = tree.visit(transformer)
    tree.validate()
    return tree


def set_verify(tree, mappings):

    import libcst as cst

    class UpdateVerify(cst.CSTTransformer):
        def leave_Call(
            self, original_node: cst.Call, updated_node: cst.Call
        ) -> cst.Call:
            if isinstance(updated_node.func, cst.Attribute):
                if updated_node.func.attr.value == "verify":
                    new_arg = cst.Arg(cst.Name(mappings["public_key"]))
                    return updated_node.with_changes(args=[new_arg, *updated_node.args])
            return updated_node

    transformer = UpdateVerify()
    tree = tree.visit(transformer)
    tree.validate()
    return tree

"""
def set_verify_cryptography(tree, mappings):
    
    import ast
    class updateVerify(ast.NodeTransformer):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == mappings["public_key"]:
                    node.

                    """