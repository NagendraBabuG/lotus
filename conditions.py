import libcst as cst
import libcst.matchers as m
from libcst.metadata import MetadataWrapper, QualifiedNameProvider


def has_ds_verify(tree: cst.Module) -> bool:
    class DSVerifyVisitor(cst.CSTVisitor):
        value = False

        def visit_Call(self, node: cst.Call):
            if m.matches(node, m.Call(func=m.Attribute(attr=m.Name("verify")))):
                self.value = True

    obj = DSVerifyVisitor()
    tree.visit(obj)
    return obj.value


def has_pycryptodome_ds_sign(tree: cst.Module) -> bool:
    class PycryptodomeDSSignVisitor(cst.CSTVisitor):
        value = False

        def visit_Call(self, node: cst.Call):
            if m.matches(node, m.Call(func=m.Attribute(attr=m.Name("sign")))):
                self.value = True

    obj = PycryptodomeDSSignVisitor()
    tree.visit(obj)
    return obj.value


def has_pycryptodome_ds_primitive(tree: cst.Module) -> bool:
    primitives = {"pkcs1_15", "pss", "eddsa", "dss"}

    class PycryptodomeDSPrimitiveVisitor(cst.CSTVisitor):
        value = False

        def visit_Call(self, node: cst.Call):
            if m.matches(node, m.Call(func=m.Attribute(value=m.Name()))):
                if isinstance(node.func, cst.Attribute) and isinstance(node.func.value, cst.Name):
                    if node.func.value.value in primitives:
                        self.value = True

    obj = PycryptodomeDSPrimitiveVisitor()
    tree.visit(obj)
    return obj.value


def has_import_pycryptodome(tree, library) -> bool:
    class ImportPycryptodomeVisitor(cst.CSTVisitor):
        value = False

        def visit_ImportFrom(self, node: cst.ImportFrom):
            if node.module is not None:
                if m.matches(node.module, m.Attribute(attr=m.Name("Cryptodome"))) or \
                   m.matches(node.module, m.Attribute(attr=m.Name("Crypto"))) or \
                   m.matches(node.module, m.Name("Cryptodome")) or \
                   m.matches(node.module, m.Name("Crypto")):
                    self.value = True

    obj = ImportPycryptodomeVisitor()
    tree.visit(obj)
    return obj.value


def has_import_cryptography(tree, library):
    class ImportCryptographyVisitor(cst.CSTVisitor):
        value = False

        def visit_ImportFrom(self, node: cst.ImportFrom):
            if node.module is not None:
                if m.matches(node.module, m.Attribute(attr=m.Name("cryptography"))) or \
                   m.matches(node.module, m.Name("cryptography")):
                    self.value = True

    obj = ImportCryptographyVisitor()
    tree.visit(obj)
    return obj.value


def has_rsa_ecc_cryptography(tree: cst.Module):
    class RSACryptographyVisitor(cst.CSTVisitor):
        value = False

        def visit_ImportFrom(self, node: cst.ImportFrom):
            if node.module is not None:
                if m.matches(node.module, m.Attribute(attr=m.Name("rsa"))) or \
                   m.matches(node.module, m.Attribute(attr=m.Name("ec"))) or \
                   m.matches(node.module, m.Name("rsa")) or \
                   m.matches(node.module, m.Name("ec")):
                    self.value = True
            for alias in node.names:
                if isinstance(alias, cst.ImportAlias) and alias.name.value in ("rsa", "ec"):
                    self.value = True

    obj = RSACryptographyVisitor()
    tree.visit(obj)
    return obj.value


def has_generate(tree: cst.Module):
    class GenerateVisitor(cst.CSTVisitor):
        value = False

        def visit_Assign(self, node: cst.Assign):
            if m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name("generate"))))):
                self.value = True

    obj = GenerateVisitor()
    tree.visit(obj)
    return obj.value


def has_generate_cryptography(tree):
    class GenerateCryptographyVisitor(cst.CSTVisitor):
        value = False

        def visit_Assign(self, node: cst.Assign):
            if m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name("generate"))))):
                self.value = True
            if m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name("generate_private_key"))))):
                self.value = True

    obj = GenerateCryptographyVisitor()
    tree.visit(obj)
    return obj.value

def has_generate_nacl(tree):
    class GenerateNaClVisitor(cst.CSTVisitor):
        METADATA_DEPENDENCIES = (QualifiedNameProvider,)
        value = False
        def __init__(self, metadata_wrapper):
            super().__init__()
            self.metadata_wrapper = metadata_wrapper
        def visit_Assign(self, node: cst.Assign):
            if not m.matches(node, m.Assign(value=m.Call())):
                return
            qualified_names = self.get_metadata(QualifiedNameProvider, node.value.func, default=None)
            if not qualified_names:
                return

            if any(q.name == "nacl.signing.SigningKey.generate" for q in qualified_names):
                self.value = True

    wrapper = MetadataWrapper(tree)
    visitor = GenerateNaClVisitor(wrapper)
    wrapper.visit(visitor)
    return visitor.value

def has_publickey(tree: cst.Module) -> bool:
    class PublicKeyVisitor(cst.CSTVisitor):
        value = False

        def visit_Assign(self, node: cst.Assign):
            if m.matches(node, m.Assign(value=m.Call(func=m.Attribute(attr=m.Name("publickey"))))):
                self.value = True

    obj = PublicKeyVisitor()
    tree.visit(obj)
    return obj.value


def has_public_key(tree: cst.Module):
    # TODO
    return False


def has_hash(mappings: dict) -> bool:
    return "message" in mappings and "hash_algo" in mappings

"""
def has_ds_sign(tree):
    #needs to update this function
    class signChecker(cst.CSTVisitor):
        value=False
        def visit_call(self, node):
            if m.matches(node, m.Call(func=m.Name(value="sign"))):
                self.value = True
    obj = signChecker()
    tree.visit(obj)

    if(obj.value == True): print("HAS sign")
    return obj.value
"""

def has_ds_sign(tree):
    class SignChecker(cst.CSTVisitor):
        METADATA_DEPENDENCIES = (QualifiedNameProvider,)
        value = False

        def __init__(self, metadata_wrapper):
            self.metadata_wrapper = metadata_wrapper

        def visit_Call(self, node):
            qualified_names = self.get_metadata(QualifiedNameProvider, node.func, default=None)
            if not qualified_names:
                return
            for qname in qualified_names:
                if(qname.name == "nacl.signing.SigningKey.sign"or qname.name.startswith("cryptography.hazmat.primitives.asymmetric")
                    or qname.name.endswith("sign")):
                    self.value = True
                    break

            if not self.value and m.matches(
                node,
                m.Call(func=m.Attribute(attr=m.Name("sign")))
            ):
                self.value = True

    wrapper = MetadataWrapper(tree)
    visitor = SignChecker(wrapper)
    wrapper.visit(visitor)
    return visitor.value