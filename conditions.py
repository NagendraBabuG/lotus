import libcst as cst


def has_ds_verify(tree):
    for node in tree.visit(cst.CSTVisitor()):
        if isinstance(node, cst.Call) and isinstance(node.func, cst.Attribute):
            if node.func.attr.value == "verify":
                return True
    return False


def has_pycryptodome_ds_sign(tree):
    for node in tree.visit(cst.CSTVisitor()):
        if isinstance(node, cst.Call) and isinstance(node.func, cst.Attribute):
            if node.func.attr.value == "sign":
                return True
    return False


def has_pycryptodome_ds_primitive(tree):
    pycryptodome_ds_primitive = {"pkcs1_15", "pss", "eddsa", "dss"}
    for node in tree.visit(cst.CSTVisitor()):
        if isinstance(node, cst.Call) and isinstance(node.func, cst.Attribute):
            if isinstance(node.func.value, cst.Name) and node.func.value.value in pycryptodome_ds_primitive:
                return True
    return False


def has_import_pycryptodome(tree):
    for node in tree.visit(cst.CSTVisitor()):
        if isinstance(node, cst.ImportFrom) and node.module is not None:
            if any(part.value in ("Cryptodome", "Crypto") for part in node.module.attr or [node.module]):
                return True
    return False


def has_import_cryptography(tree) :
    for node in tree.visit(cst.CSTVisitor()):
        if isinstance(node, cst.ImportFrom) and node.module is not None:
            if any(part.value == "cryptography" for part in node.module.attr or [node.module]):
                return True
    return False


def has_rsa_ecc_cryptography(tree):
    for node in tree.visit(cst.CSTVisitor()):
        if isinstance(node, cst.ImportFrom) and node.module is not None:
            parts = [node.module.value] if isinstance(node.module, cst.Name) else [p.value for p in node.module.attr or []]
            if "rsa" in parts or "ec" in parts:
                return True
            else:
                for alias in node.names:
                    if isinstance(alias, cst.ImportAlias) and alias.name.value in ("rsa", "ec"):
                        return True
    return False


def has_generate(tree):
    for node in tree.visit(cst.CSTVisitor()):
        if isinstance(node, cst.Assign) and isinstance(node.value, cst.Call):
            if isinstance(node.value.func, cst.Attribute) and node.value.func.attr.value == "generate":
                return True
    return False


def has_generate_cryptography(tree):
    for node in tree.visit(cst.CSTVisitor()):
        if isinstance(node, cst.Assign) and isinstance(node.value, cst.Call):
            if isinstance(node.value.func, cst.Attribute) and node.value.func.attr.value in ("generate", "generate_private_key"):
                return True
    return False


def has_publickey(tree):
    for node in tree.visit(cst.CSTVisitor()):
        if isinstance(node, cst.Assign) and isinstance(node.value, cst.Call):
            if isinstance(node.value.func, cst.Attribute) and node.value.func.attr.value == "publickey":
                return True
    return False
