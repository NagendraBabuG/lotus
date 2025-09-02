import libcst as cst
import libcst.matchers as m
from libcst.metadata import MetadataWrapper, QualifiedNameProvider
import random, string


class DSTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (QualifiedNameProvider,)

    assymAlgos = {"RSA", "ECC"}
    algoMap = {}
    impStmts = []
    classical_to_pqc_sign = {
    "ECC-256": [
        "MLDSA_44",
        "FALCON_512"
    ],
    "ECC-384": [
        "MLDSA_65"
    ],
    "ECC-521": [
        "MLDSA_87",
        "FALCON_1024"
    ],
    "RSA-1024": [
        "MLDSA_65",
        "FALCON_1024"
    ],
    "RSA-2048": [
        "MLDSA_87",
        "FAST_SPHINCS",
        "SMALL_SPHINCS"
    ]}
    prvToPub = {}            # private -> public key mapping
    oldToNewVarName = {}   
    #pqcAssymAlgos= ["MLDSA_44","MLDSA_65","MLDSA_87","FALCON_512","FALCON_1024","FAST_SPHINCS","SMALL_SPHINCS"]
    choosenDs = None

    def leave_Assign(self, original_node, updated_node):
        if not m.matches(original_node.value, m.Call()):
            return updated_node

        qualified_names = self.get_metadata(QualifiedNameProvider, original_node.value.func, default=None)
        if not qualified_names:
            return updated_node

        qualified_names = [q.name for q in qualified_names]
        if any(name == "Crypto.PublicKey.RSA.generate" for name in qualified_names):
            keysize = str(original_node.value.args[0].value.value)  

            classical_algo =  "RSA-" + keysize

            ind = random.randint(0, len(self.classical_to_pqc_sign[classical_algo])-1)
            pqc_algo = self.classical_to_pqc_sign[classical_algo][ind]
            
            prvKey = original_node.targets[0].target.value
            pubKey = "pub_key_"+ genRandStr()
            self.oldToNewVarName[pubKey] = "publicKey" + str(len(self.prvToPub) + 1)
            self.prvToPub[prvKey] = pubKey
            
            import_stmt = cst.ImportFrom(
                module=cst.Attribute(value=cst.Name("quantcrypt"),
                attr=cst.Name("dss"),),
                names=[cst.ImportAlias(name=cst.Name(pqc_algo))]
            )
            self.impStmts.append(import_stmt)
            new_assign = cst.parse_statement(
                f"{pubKey}, {prvKey} = {pqc_algo}().keygen()"
            ).body[0]
            return new_assign

        if any(name == "Crypto.PublicKey.ECC.generate" for name in qualified_names):
            keysize = str(original_node.value.args[0].value.value)
            classical_algo =  "ECC-" + keysize

            ind = random.randint(0, len(self.classical_to_pqc_sign[classical_algo])-1)
            pqc_algo = self.classical_to_pqc_sign[classical_algo][ind]
            """
            import_stmt = cst.ImportFrom(
                module=cst.Name("quantcrypt.dss"),
                names=[cst.ImportAlias(name=cst.Name(pqc_algo))],
                level=0,
                )
            """
            import_stmt = cst.ImportFrom(
                module=cst.Attribute(value=cst.Name("quantcrypt"),
                attr=cst.Name("dss"),),
                names=[cst.ImportAlias(name=cst.Name(pqc_algo))]
            )

            self.impStmts.append(import_stmt)
            
            new_assign = cst.parse_statement(
                f"{original_node.targets[0].target.value}, _ = {pqc_algo}().keygen()"
            ).body[0]
            return new_assign

        return updated_node


def addPQCImp(self, importStmts):
    pass

def genRandStr(len = 3):
    #Generates random string of length len
    return ''.join(random.choices(string.ascii_letters, k = len))

def main(source: str):
    module = cst.parse_module(source)
    wrapper = MetadataWrapper(module)

    transformer = DSTransformer()
    new_tree = wrapper.visit(transformer)

    print(new_tree.code)


if __name__ == "__main__":
    with open('./test1.py', 'r') as f:
        source = f.read()
        print("Modified Source Code: ")
        main(source)