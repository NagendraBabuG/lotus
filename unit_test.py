import os
import subprocess
import sys
import glob
import ast


def has_func_or_class(file_path):
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read(), filename=file_path)
            if any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree)):
                return True
            if any(isinstance(node, ast.ClassDef) for node in ast.walk(tree)):
                return True
            return False
    except Exception as e:
        print(f"Error : {e}")
        return False

def make_dirs(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def run_pynguin(project_path, output_path, module_name):
    make_dirs(output_path, 'pynguin-report')
    cmd = f"pynguin --project-path {project_path} --output-path {output_path} --module-name {module_name} --maximum-iterations 10000 --algorithm RANDOM --create-coverage-report -v"
    try:
        subprocess.run(cmd, shell=True, check=True)
    except Exception as e:
        print(f"Error: Pynguin failed to generate tests for {project_path}/{module_name}.py: {e}")
        
def modify_imports(test_file, new_path, old_module, new_module):
    try:
        with open(test_file, 'r') as f:
            content = f.read()
        content = content.replace(f'import {old_module}', f'import sys\nsys.path.insert(0, "{os.path.abspath(new_path)}")\nimport {new_module}')
        with open(test_file, 'w') as f:
            f.write(content)
    except FileNotFoundError:
        print(f"Error: Test file {test_file} not found. Stopping execution.")
        sys.exit(1)

def run_tests(test_file):
    try:
        result = subprocess.run(f"pytest {test_file} -v", shell=True, capture_output=True, text=True)
        print(result.stdout)
        return result.returncode == 0
    except Exception as e:

        print(f"Test execution failed for {test_file}: {e}")
        return False

def get_files(directory):
    return [f for f in glob.glob(f"{directory}/*.py")]

def get_mod_name(file_path):
    return os.path.splitext(os.path.basename(file_path))[0]

make_dirs('./tests/source_tests', './tests/refactored_tests', './pynguin-report')

file_mapping = {
    'test2': 'test2',
    'test1': 'test1'
    }

source_files = get_files('./test/source')
refactored_files = get_files('./test/target')

for source_file in source_files:

    if not has_func_or_class(source_file):
        print("File doesn't have testable usecases ", source_file)
        continue

    module_name = get_mod_name(source_file)
    print(f"Generating tests for source module: {module_name}")
    run_pynguin('./test/source', './tests/source_tests', module_name)

for refactored_file in refactored_files:

    if not has_func_or_class(refactored_file):
        print("File doesn't have testable usecases ", refactored_file)
        continue
    module_name = get_mod_name(refactored_file)
    print(f"Generating tests for refactored module: {module_name}")
    run_pynguin('./test/target', './tests/refactored_tests', module_name)

# Testing
for source_file in source_files:
    source_module = get_mod_name(source_file)
    refactored_module = file_mapping.get(source_module, source_module)
    test_file = f'./tests/source_tests/test_{source_module}.py'
    
    print(f"Cross-testing {source_module} tests against {refactored_module}")
    modify_imports(test_file, './test/refactored', source_module, refactored_module)
    if not run_tests(test_file):
        print(f"Source tests failed on refactored module {refactored_module}")
        all_tests_pass = False

for refactored_file in refactored_files:
    refactored_module = get_mod_name(refactored_file)
    source_module = next((k for k, v in file_mapping.items() if v == refactored_module), refactored_module)
    test_file = f'./tests/refactored_tests/test_{refactored_module}.py'
    
    print(f"Testing {refactored_module} tests against {source_module}")
    modify_imports(test_file, './test/source', refactored_module, source_module)
    if not run_tests(test_file):
        print(f"Refactored tests failed on source module {source_module}")
