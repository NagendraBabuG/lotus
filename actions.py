import libcst as cst
import libcst.matchers as m

from libcst.metadata import FullyQualifiedNameProvider, FullRepoManager, QualifiedNameProvider, MetadataWrapper

temp_map = {}


def return_empty_list(tree):
    return []

def return_tree(tree):
    return tree
def set_primitive(tree):
    #needs to add
    return tree

def add_hash_nodes(tree):
    #needse to add
    return tree

def remove_public_key(tree, mappings):
    #needs to add
    return tree

def update_imports_cryptography(tree):
    return tree
def record_keypair_ids_nacl(tree):
    mappings = {}

    class CheckNaClImport(cst.CSTVisitor):
        METADATA_DEPENDENCIES = (QualifiedNameProvider,)

        def __init__(self, metadata_wrapper):
            super().__init__()
            self.metadata_wrapper = metadata_wrapper

        def visit_Assign(self, node):
            if not m.matches(node, m.Assign(value=m.Call())) and not m.matches(node, m.Assign(value=m.Attribute())):
                return

            qualified_names = self.get_metadata(QualifiedNameProvider, node.value.func if m.matches(node, m.Assign(value=m.Call())) else node.value, default=None)
            if not qualified_names:
                return

            qualified_names = [q.name for q in qualified_names]

            if any(name == "nacl.signing.SigningKey.generate" for name in qualified_names):
                if isinstance(node.targets[0].target, cst.Name):
                    mappings["private_key"] = node.targets[0].target.value

            elif any(name == "nacl.signing.SigningKey.verify_key" for name in qualified_names):
                if isinstance(node.targets[0].target, cst.Name):
                    mappings["public_key"] = node.targets[0].target.value

        def visit_Call(self, node):
            if not isinstance(node.func, cst.Attribute):
                return

            qualified_names = self.get_metadata(QualifiedNameProvider, node.func, default=None)
            if not qualified_names:
                return

            qualified_names = [q.name for q in qualified_names]
            print(qualified_names, "names")

            if any(name.endswith("sign") for name in qualified_names):
                if node.args:
                    arg = node.args[0]
                    mappings["message"] = arg.value.value
                   
                if isinstance(node.func.value, cst.Name):
                    mappings["signing_key"] = node.func.value.value

                if hasattr(node, "_parent_node") and m.matches(node._parent_node, m.Assign()):
                    for target in node._parent_node.targets:
                        if isinstance(target.target, cst.Name):
                            mappings["signature"] = target.target.value

            elif any(name == "nacl.signing.VerifyKey.encode" for name in qualified_names):
               
                if hasattr(node, "_parent_node") and m.matches(node._parent_node, m.Assign()):
                    for target in node._parent_node.targets:
                        if isinstance(target.target, cst.Name):
                            mappings["verifying_key"] = target.target.value

    wrapper = MetadataWrapper(tree)
    visitor = CheckNaClImport(wrapper)
    wrapper.visit(visitor)
    return mappings

def record_keypair_ids_cryptography(tree):
    mappings={}
    class checkImport(cst.CSTVisitor):
        def visit_Assign(self, node):
            if m.matches(node, m.Assign(value=m.Call(func=m.Attribute(value=m.Name(value="rsa"))))) or \
            m.matches(node, m.Assign(value=m.Call(func=m.Attribute(value=m.Name(value="ec"))))):
                if node.value.func.attr.value=="generate_private_key":
                    mappings["private_key"] = node.targets[0].target.value
            elif m.matches(node, m.Assign(value=m.Attribute(value=m.Name(value="rsa")))) or\
            m.matches(node, m.Assign(value=m.Call(func=m.Attribute(value="ec")))):
                if node.value.func.attr.value == "generate":
                    mappings["private_key"]=node.targets[0].target.value

            elif m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name(value="public_key"))))) or\
            m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name(value="publickey"))))):
                mappings["public_key"] = node.targets[0].target.value

        def visit_Call(self, node):
            if isinstance(node.func, cst.Attribute) and isinstance(node.func.value, cst.Name):
                if node.func.value.value == "hashes":
                    mappings["hash_algo"]=node.func.attr.value
                    mappings["digest_id"] = "digest"
                elif node.func.value.value == "sign":
                    mappings["message"]=node.args[0].value.value
                    mappings["signing_key"] = node.func.value.value
                if node.func.value.value == "verify":
                    mappings["signature"]=node.args[0].value.value
                    mappings["verifying_key"] = node.func.value.value


    obj = checkImport()
    tree.visit(obj)
    return mappings

def remove_publickey(tree, mappings):


    class RemovePublicKey(cst.CSTTransformer):
        def leave_Assign(self, original_node, updated_node):
            if isinstance(updated_node.value, cst.Call):
                if isinstance(updated_node.value.func, cst.Attribute) and updated_node.value.func.attr.value == "publickey":
                    return cst.RemoveFromParent()
            return updated_node

    transformer = RemovePublicKey()
    tree = tree.visit(transformer)
    #tree.validate()
    return tree



def has_generate_cryptography(tree):
    class keywordChecker(cst.CSTVisitor):
        value = False
        def visit_Assign(self, node):
            if m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name(value="generate"))))) or \
               m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name(value="generate_private_key"))))):
                self.value = True

    obj = keywordChecker()
    tree.visit(obj)
    return obj.value


def has_publickey(tree):
    class pkeyChecker(cst.CSTVisitor):
        value = False
        def visit_Assign(self, node):
            if m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name(value="publicKey"))))):
                self.value = True

    obj = pkeyChecker()
    tree.visit(obj)
    return obj.value


def set_sign_cryptography(tree, mappings):
    class updateSign(cst.CSTTransformer):
        METADATA_DEPENDENCIES = (QualifiedNameProvider,)

        def leave_Assign(self, node, updated_node):
            qualified_names = self.get_metadata(QualifiedNameProvider, node.value)
            qnames_array = [q.name for q in qualified_names]

            if any(name==f"{mappings['private_key']}.sign" for name in qnames_array) \
            or m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name(value="sign"))))):
                new_value = f"Dilithium().sign({mappings['signing_key']}, {mappings['digest_id']})"
                return updated_node.with_changes(value=(cst.parse_statement(new_value).body[0].value))
            return updated_node

    wrapper = MetadataWrapper(tree)
    obj = updateSign()
    tree = wrapper.visit(obj)
    return tree



def set_sign_nacl(tree, mappings):
    class UpdateSignNaCl(cst.CSTTransformer):
        METADATA_DEPENDENCIES = (QualifiedNameProvider,)

        def leave_Assign(self, node, updated_node):
            if not m.matches(node, m.Assign(value=m.Call())):
                return updated_node

            qualified_names = self.get_metadata(QualifiedNameProvider, node.value.func, default=None)
            qnames_array = [q.name for q in qualified_names] if qualified_names else []

            if qualified_names:
                print(f"Qualified names for node: {qnames_array}")

            if (
                any(name.endswith("sign") for name in qnames_array)):
                
                if "signing_key" not in mappings or "message" not in mappings:
                    print(f"Missing mappings: {mappings}")
                    return updated_node
                new_value = f"Dilithium().sign({mappings['signing_key']}, {mappings['message']})"
                try:
                    print("in adding new node")
                    new_node = updated_node.with_changes(value=cst.parse_statement(new_value).body[0].value)
                    print(f"Transformed node to: {new_value}")
                    return new_node
                except Exception as e:
                    print(f"Error parsing new value: {e}")
                    return updated_node

            return updated_node

    wrapper = MetadataWrapper(tree)
    obj = UpdateSignNaCl()
    tree = wrapper.visit(obj)
    return tree
def set_keygen_node_cryptography(tree, mappings):
    class UpdateKeygen(cst.CSTTransformer):
        METADATA_DEPENDENCIES = (QualifiedNameProvider,)

        def leave_Assign(self, node, updated_node):
            qualified_names = self.get_metadata(QualifiedNameProvider, node.value)
            qnames_array = [q.name for q in qualified_names]

            if (
                any(
                    name == "cryptography.hazmat.primitives.asymmetric.ec.generate_private_key"
                    for name in qnames_array
                )
                or m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name("generate_private_key")))))
                or m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name("generate")))))
            ):
                if "public_key" not in mappings or "private_key" not in mappings:
                    print("Both 'public_key' and 'private_key' must be present in mappings\n")
                    return updated_node

                new_assign = f"{mappings['public_key']}, {mappings['private_key']} = Dilithium().keygen()"
                return cst.parse_statement(new_assign).body[0]

            return updated_node

    wrapper = MetadataWrapper(tree)
    obj = UpdateKeygen()
    tree = wrapper.visit(obj)
    return tree

def set_keygen_node_nacl(tree, mappings):
    class UpdateKeygenNaCl(cst.CSTTransformer):
        METADATA_DEPENDENCIES = (QualifiedNameProvider,)

        def leave_Assign(self, node, updated_node):
            qualified_names = self.get_metadata(QualifiedNameProvider, node.value, default=None)
            qnames_array = [q.name for q in qualified_names] if qualified_names else []

            if (
                any(name == "nacl.signing.SigningKey.generate" for name in qnames_array)
                or m.matches(
                    node,
                    m.Assign(
                        value=m.Call(
                            func=m.Attribute(
                                value=m.Name("SigningKey"),
                                attr=m.Name("generate")
                            )
                        )
                    )
                )
            ):
                if "public_key" not in mappings or "private_key" not in mappings:
                    print("Both 'public_key' and 'private_key' must be present in mappings\n")
                    return updated_node

                new_assign = f"{mappings['public_key']}, {mappings['private_key']} = Dilithium().keygen()"
                return cst.parse_statement(new_assign).body[0]

            return updated_node

    wrapper = MetadataWrapper(tree)
    obj = UpdateKeygenNaCl()
    tree = wrapper.visit(obj)
    return tree


def set_verify_cryptography(tree, mappings):
    class updateVerify(cst.CSTTransformer):
        METADATA_DEPENDENCIES = (QualifiedNameProvider,)

        def leave_Assign(self, node, updated_node):
            qualified_names = self.get_metadata(QualifiedNameProvider, node.value)
            qnames_array = [q.name for q in qualified_names]

            if any(mappings['verifying_key']+'.verify' for name in qnames_array) \
            or m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name(value="verify"))))):
                new_assign = [node.targets[0].target.value + " = Dilithium().verify(mappings['verifying_key'], mappings['digest_id'], mappings['signature'])"]
                return cst.parse_statement(new_assign).body[0]
            return updated_node

        def leave_Expr(self, node, updated_node):
            qualified_names = self.get_metadata(QualifiedNameProvider, node.value)
            qnames_array = [q.name for q in qualified_names]

            if any(mappings['verifying_key']+'.verify' for name in qnames_array) \
            or m.matches(node, m.Expr(value=m.Call(func=m.Attribute(attr=m.Name(value="verify"))))):
                new_expr = "Dilithium().verify(mappings['verifying_key'], mappings['digest_id'], mappings['signature'])"
                return cst.parse_statement(new_expr).body[0]
            return updated_node

    wrapper = MetadataWrapper(tree)
    obj = updateVerify()
    tree = wrapper.visit(obj)
    return tree


"""
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


def set_verify_cryptography(tree, mappings):
    
    import ast
    class updateVerify(ast.NodeTransformer):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == mappings["public_key"]:
                    node.

                    """

