import ast, random, string

class updateAssym(ast.NodeTransformer):
    prvToPub = {} #Stores the name of the publicKeys w.r.t to the corresponding privateKeys
    isCryptoIncluded = False
    oldToNewVarName = {}
    assymAlgos = {"RSA", "ECC"}
    algoMap = {}
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
    
    #pqcAssymAlgos= ["MLDSA_44","MLDSA_65","MLDSA_87","FALCON_512","FALCON_1024","FAST_SPHINCS","SMALL_SPHINCS"]
    choosenDs = None
    importStmts = []
    def visit_Assign(self, node):
        match node:
            case ast.Assign(value = ast.Call(func = ast.Attribute(value = ast.Name(id = id_name), attr='generate'), args=args)):
                if id_name not in self.assymAlgos: return node
                # handle the case of "key = someAssymAlgo.generate()"
                self.isCryptoIncluded = True
                prvKey = node.targets[0].id
                pubKey = genRandStr()
                self.oldToNewVarName[pubKey] = "publicKey" + str(len(self.prvToPub)+1)
                self.prvToPub[prvKey] = pubKey
                keysize = str(args[0].value)
                classical_algo = id_name + "-" + keysize

                ind = random.randint(0, len(self.classical_to_pqc_sign[classical_algo])-1)
                pickAlgo = self.classical_to_pqc_sign[classical_algo][ind]
                self.choosenDs= pickAlgo

                
                self.algoMap[classical_algo] = [pickAlgo]
                
                            
                self.importStmts.append(ast.ImportFrom(module="quantcrypt.dss",names=[ast.alias(name=pickAlgo, asname=None)],level=0)
        )
                return ast.parse(f"{pubKey}, {prvKey} = {pickAlgo}().keygen()")

            case ast.Assign(value = ast.Call(func = ast.Attribute(value = ast.Name(), attr = attr))):
                if attr not in {"public_key", "publickey"}: return node
                # handle the case of "publicKey = privateKey.publickey()"
                prvKey = node.value.func.value.id
                pubKey = node.targets[0].id
                if prvKey in self.prvToPub:
                    self.oldToNewVarName[self.prvToPub[prvKey]] = pubKey
                    return ast.parse("")
                return node
            case ast.Assign(targets=[ast.Name(id=lhs)],value=ast.Call(func=ast.Attribute(value=ast.Call(func=ast.Attribute(value=ast.Name(id="pkcs1_15"), attr="new"),
                args=[ast.Name(id=prvKey)]),attr="sign"),args=[ast.Name(id=hash_obj)])):
                new_rhs = ast.parse(f"{lhs} = {self.choosenDs}().sign({prvKey}, message)").body[0].value
                node.value = new_rhs
                return node
            
        return node
    def visit_Expr(self, node):
        match node:
            case ast.Expr(value=ast.Call(func=ast.Attribute(value=ast.Call(func=ast.Attribute(value=ast.Name(id="pkcs1_15"), attr="new"),
                            args=[ast.Name(id=pubKey)]),attr="verify"),args=[ast.Name(id=hash_obj), ast.Name(id=sigName)])):
                node.value = ast.parse(f"{self.choosenDs}().verify({pubKey}, message, {sigName})").body[0].value
                return node
        return node


class nameUpdater(ast.NodeTransformer):
    def __init__(self, oldToNewVarName):
        self.oldToNewVarName = oldToNewVarName
    def visit_Name(self, node):
        if node.id in self.oldToNewVarName:
            node.id = self.oldToNewVarName[node.id]
        return node

def genRandStr(len = 20):
    #Generates random string of length len
    return ''.join(random.choices(string.ascii_letters, k = len))

def rmClassicalCryptoLib(source_code):
    pass

def addPQCLib(tree, importStmts):
    #needs to add functionality for checking there is no duplicate imports statements
    tree.body = importStmts + tree.body
    return tree


def main(source_code):
    ast_tree = ast.parse(source_code)
    rmClassicalCryptoLib(ast_tree)
    assymUpdater = updateAssym()
    ast_tree = assymUpdater.visit(ast_tree)
    addPQCLib(ast_tree, assymUpdater.importStmts)
    ast_tree = nameUpdater(assymUpdater.oldToNewVarName).visit(ast_tree)
    print(ast.unparse(ast_tree))


if __name__ == "__main__":
    
    with open('./test1.py', 'r') as f:
        source = f.read()
        print("Modified Source Code: ")
        main(source)

# myAssymAlgo = RSA.generate(1024).publickey();
