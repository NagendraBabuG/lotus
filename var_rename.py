import ast
import random

class FuncVarNameRefactator:
    def __init__(self):
        self.code_identifiers = [
            "key", "public_key", "signature", "b64_signature", "verifier", "decoded_message"
        ]
        self.identifiers = {
            'keygen': ["key_generator", "keygen_function", "generate_keys"],
            'sign': ['signing_function', 'sign_function', 'sign_generation', 'signer'],
            'verify': ['verifying_function', 'verify_function', 'sign_verification', "verifier"],
            'key': ['api_key', 'signing_key', 'pri_key', 'private_key', 'key'],
            'public_key': ['public_api_key', 'verifying_key', 'pub_key', 'public_key'],
            'message': ['data', 'payload', 'plaintext', 'message'],
            'signature': ['signed_data', 'signed', 'digital_signature', 'signature'],
            'b64_signature': ["b64_signature", "sigb64", "signed_b64", "b64_result", "b64_data", "final_b64"],
            'verifier': ["validator", "verify_object", "ver_obj"],
            'decoded_message': ["decoded", "signed_message", "dec_msg"]
        }
        self.algorithms = {'signatures': ["pkcs1_v1_5", "pss", "DSS", "eddsa"]}
        self.key_types = ['DSA', 'RSA', 'ECC']
        self.key_sizes = [256, 512, 1024, 2048, 4096]
        self.ecc_key_sizes = ['p192', 'p224', 'p256', 'p384', 'p521']

        self.old_names = {}     # Map old identifiers to new ones
        self.func_param_maps = {}  # Map function names to original→new param name mapping

    def mutate_code(self, source_code):
        if isinstance(source_code, bytes):
            source_code = source_code.decode("utf-8")

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")

        self.old_names = {}
        self.func_param_maps = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                old_func_name = node.name
                node.name = random.choice(self.identifiers.get(old_func_name, [old_func_name]))
                self.old_names[old_func_name] = node.name

                # Shuffle parameters and rename them
                original_params = [arg.arg for arg in node.args.args]
                shuffled_params = original_params.copy()
                random.shuffle(shuffled_params)

                param_map = dict(zip(original_params, shuffled_params))
                self.func_param_maps[node.name] = param_map

                for arg in node.args.args:
                    arg.arg = param_map[arg.arg]

            elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if (isinstance(node.value.func, ast.Attribute) and
                    len(node.targets) > 0 and 
                    isinstance(node.targets[0], ast.Name) and 
                    node.targets[0].id in self.code_identifiers and 
                    node.targets[0].id not in self.old_names):
                    method_choice = random.choice(self.identifiers.get(node.targets[0].id, [node.targets[0].id]))
                    self.old_names[node.targets[0].id] = method_choice
                    node.targets[0].id = method_choice

            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "new":
                    node.args = [arg for arg in node.args if not (
                        isinstance(arg, ast.Constant) and 
                        arg.value in ["fips-186-3", "rfc8032"]
                    )]
                    method_choice = random.choice(self.algorithms['signatures'])
                    node.func.value.id = method_choice
                    if method_choice == "DSS":
                        node.args.append(ast.Constant(value="fips-186-3"))
                    elif method_choice == "eddsa":
                        node.args.append(ast.Constant(value="rfc8032"))

                elif node.func.attr == "generate":
                    node.func.value.id = random.choice(self.key_types)
                    for kw in node.keywords:
                        if node.func.value.id == "ECC":
                            kw.arg = "curve"
                            kw.value = ast.Constant(value=random.choice(self.ecc_key_sizes))
                    for arg in node.args:
                        if isinstance(arg, ast.Constant):
                            arg.value = random.choice(
                                self.ecc_key_sizes if node.func.value.id == "ECC" else self.key_sizes
                            )

        # Rename all identifier usages
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in self.old_names:
                node.id = self.old_names[node.id]

        # Reorder function call arguments to match shuffled parameter order
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.func_param_maps:
                    param_map = self.func_param_maps[func_name]
                    original_params = list(param_map.keys())
                    new_param_order = list(param_map.values())

                    # Keep the arguments in the same original order, just shuffle position
                    reordered_args = [None] * len(new_param_order)
                    for idx, arg in enumerate(node.args):
                        if idx < len(reordered_args):
                            reordered_args[idx] = arg
                    node.args = reordered_args

        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def crossover_code(self, code1, code2):
        split1 = code1.split("\n")
        split2 = code2.split("\n")
        crossover_point = random.randint(1, min(len(split1), len(split2)) - 1)
        return "\n".join(split1[:crossover_point] + split2[crossover_point:])

    def generate_variants(self, initial_code, generations=2, population_size=2):
        population = [initial_code]
        final_population = []

        for _ in range(generations):
            mutated_code = self.mutate_code(initial_code)
            final_population.append(mutated_code)

            new_population = []
            while len(new_population) < population_size:
                parent_code = random.choice(population)
                mutated_code = self.mutate_code(parent_code)
                new_population.append(mutated_code)

            population = new_population

        return final_population

    def get_refactored_code(self, source_code):
        try:
            return self.mutate_code(source_code)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
