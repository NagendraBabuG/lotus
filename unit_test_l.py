import os
import subprocess
import sys
import glob
import ast
import re

RESULT_LOG = "tests_result.txt"

def log_result(source_module, target_module, result, status):
    with open(RESULT_LOG, 'a', encoding='utf-8') as f:
        f.write(f"[SRC→REF] Source: {source_module} | Target: {target_module} | Result: {status}\n")

def has_func_or_class(file_path):
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read(), filename=file_path)
            return any(isinstance(node, (ast.FunctionDef, ast.ClassDef)) for node in ast.walk(tree))
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return False

def make_dirs(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def run_pynguin(project_path, output_path, module_name):
    project_path = os.path.abspath(project_path)
    output_path = os.path.abspath(output_path)
    
    if not os.path.exists(project_path):
        print(f"Error: Project path {project_path} does not exist.")
        return
    if not os.access(project_path, os.R_OK):
        print(f"Error: No read permission for {project_path}.")
        return
    make_dirs(output_path)
    if not os.access(output_path, os.W_OK):
        print(f"Error: No write permission for {output_path}.")
        return

    cmd = [
        sys.executable, 
        "-m", "pynguin",
        "--project-path", project_path,
        "--output-path", output_path,
        "--module-name", module_name,
        "--maximum-iterations", "10000",
        "--algorithm", "DYNAMOSA",
        "--create-coverage-report",
        "-v"
    ]
    env = os.environ.copy()
    env["PYNGUIN_DANGER_AWARE"] = "1"
    try:
        process = subprocess.run(cmd, env=env, check=True, stderr=subprocess.PIPE, text=True)
        if process.stderr:
            print(f"Pynguin stderr output: {process.stderr}")
        test_file = os.path.join(output_path, f"test_{module_name}.py")
        if os.path.exists(test_file):
            clean_test_file(test_file)
    except subprocess.CalledProcessError as e:
        print(f"Error: Pynguin failed to generate tests for {project_path}/{module_name}.py: {e}")
        print(f"Pynguin stderr: {e.stderr}")
    except Exception as e:
        print(f"Error in run_pynguin for {module_name}: {e}")

def clean_test_file(test_file):
    try:
        with open(test_file, 'r') as f:
            lines = f.readlines()

        used_aliases = set()
        for line in lines:
            used_aliases.update(re.findall(r'\bmodule_(\d+)', line))

        new_lines = []
        seen_imports = set()
        has_pytest = False
        for line in lines:
            if line.strip().startswith('import pytest'):
                has_pytest = True
                new_lines.append(line)
                seen_imports.add(line.strip())
                continue
            if (line.strip().startswith('sys.path.insert') or
                re.match(r'^\s*import\s+\w+\s+as\s+module_\d+', line)):
                new_lines.append(line)
                seen_imports.add(line.strip())
                continue
            if re.match(r'^\s*import\s+(\w+)\s+as\s+\1', line):
                continue
            if line.strip().startswith('import ') and line.strip() in seen_imports:
                continue
            new_lines.append(line)
            seen_imports.add(line.strip())

        if not has_pytest:
            new_lines.insert(0, "import pytest\n")

        with open(test_file, 'w') as f:
            f.writelines(new_lines)
        print(f"Cleaned up test file {test_file}")
        with open(test_file, 'r') as f:
            print(f"Content of {test_file} after cleaning:\n{f.read()}\n")
        print(f"Detected module aliases in {test_file}: {', '.join(f'module_{num}' for num in sorted(used_aliases))}")
        return True
    except Exception as e:
        print(f"Error cleaning test file {test_file}: {e}")
        return False

def modify_imports(test_file, new_path, old_module, new_module):
    try:
        with open(test_file, 'r') as f:
            lines = f.readlines()

        used_aliases = set()
        for line in lines:
            used_aliases.update(re.findall(r'\bmodule_(\d+)', line))

        new_lines = []
        has_pytest = False
        for line in lines:
            if line.strip().startswith('import pytest'):
                has_pytest = True
                new_lines.append(line)
            elif not (line.strip().startswith('import ') or line.strip().startswith('sys.path.insert')):
                new_lines.append(line)

        formatted_path = new_path.replace('\\\\', '/').replace('C:', 'C:/')
        new_lines.insert(0, f"import sys\n")
        new_lines.insert(1, f'sys.path.insert(0, "{formatted_path}")\n')
        insert_idx = 2
        for alias_num in sorted(used_aliases):
            new_lines.insert(insert_idx, f"import {new_module} as module_{alias_num}\n")
            insert_idx += 1
        if not has_pytest:
            new_lines.insert(insert_idx, "import pytest\n")

        with open(test_file, 'w') as f:
            f.writelines(new_lines)

        print(f"Modified imports in {test_file} to use {new_module} from {new_path}")
        with open(test_file, 'r') as f:
            print(f"Content of {test_file} after modifying imports:\n{f.read()}\n")
        print(f"Added imports for module aliases in {test_file}: {', '.join(f'module_{num}' for num in sorted(used_aliases))}")
        return True
    except FileNotFoundError:
        print(f"Error: Test file {test_file} not found. Skipping.")
        return False
    except Exception as e:
        print(f"Error modifying imports in {test_file}: {e}")
        return False

def run_tests(test_file):
    try:
        with open(test_file, 'r') as f:
            content = f.read()
            if 'import pytest' not in content:
                print(f"Error: 'import pytest' missing in {test_file}. Aborting test run.")
                return False
            used_aliases = set(re.findall(r'\bmodule_(\d+)', content))
            for alias_num in used_aliases:
                if f'import ' not in content or f' as module_{alias_num}' not in content:
                    print(f"Error: 'import ... as module_{alias_num}' missing in {test_file}. Aborting test run.")
                    return False
        cmd = [sys.executable, "-m", "pytest", test_file, "-v"]
        print(f"Pytest command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Python version used for pytest: {sys.executable}")
        if result.stderr:
            print(f"Pytest stderr output: {result.stderr}")
        print(result.stdout)
        return result.returncode == 0
    except Exception as e:
        print(f"Test execution failed for {test_file}: {e}")
        return False

def get_files(directory):
    return [f for f in glob.glob(os.path.join(os.path.abspath(directory), "*.py"))]

def get_mod_name(file_path, is_refactored=False):
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    if is_refactored:
        # Remove pipno_X_ prefix if present
        match = re.match(r'pipno_\d+_(.*)', base_name)
        return match.group(1) if match else base_name
    return base_name

# Initialize log file
with open(RESULT_LOG, 'w', encoding='utf-8') as f:
    f.write("Test Results Log\n")
    f.write("=" * 60 + "\n")

# Define directories
source_dir = os.path.expanduser("~/Desktop/pqc/refactor/input/cryptome/excuted")
refactored_dir = os.path.expanduser("~/Desktop/pqc/refactor/output/cryptodoke/excuted")
make_dirs(os.path.join(source_dir), os.path.join(refactored_dir), './tests/source_tests', './pynguin-report')

# Get source and refactored files
source_files = get_files(source_dir)
refactored_files = get_files(refactored_dir)

# Create mapping between source and refactored modules
source_module_names = {get_mod_name(f) for f in source_files}
refactored_module_names = {get_mod_name(f, is_refactored=True) for f in refactored_files}
file_mapping = {
    source_name: refactored_name
    for source_name in source_module_names
    for refactored_name in refactored_module_names
    if source_name == refactored_name
}

# Log file mapping
with open('filemap.txt', 'a') as f:
    f.write(str(file_mapping) + "\n")

all_tests_pass = True

# Generate tests for source files
for source_file in source_files:
    if not has_func_or_class(source_file):
        print(f"File doesn't have testable usecases: {source_file}")
        continue
    module_name = get_mod_name(source_file)
    print(f"Generating tests for source module: {module_name}")
    run_pynguin(source_dir, './tests/source_tests', module_name)

# Run and compare tests on refactored code
for source_file in source_files:
    source_module = get_mod_name(source_file)
    refactored_module = file_mapping.get(source_module, None)

    if not refactored_module:
        print(f"No matching refactored module for {source_module}. Skipping.")
        continue

    test_file = os.path.join('./tests/source_tests', f"test_{source_module}.py")
    print(f"\n=== Testing {source_module} against refactored {refactored_module} ===")

    if not os.path.exists(test_file):
        print(f"Test file {test_file} not found. Skipping.")
        log_result(source_module, refactored_module, False, "FAIL (Missing Test)")
        continue

    # Find the actual refactored file with pipno_X_ prefix
    refactored_file = next(
        (f for f in refactored_files if get_mod_name(f, is_refactored=True) == refactored_module),
        None
    )
    if not refactored_file or not os.path.exists(refactored_file):
        print(f"Refactored module {refactored_module} not found. Skipping.")
        log_result(source_module, refactored_module, False, "FAIL (Missing Refactored Module)")
        all_tests_pass = False
        continue

    print(f"Running tests on refactored: {refactored_module}")
    if not modify_imports(test_file, refactored_dir, source_module, refactored_module):
        log_result(source_module, refactored_module, False, "FAIL (Import Modification)")
        all_tests_pass = False
        continue
    refactored_result = run_tests(test_file)

    if refactored_result:
        print(f"Behavior matches expected (source-derived) for {source_module}")
        log_result(source_module, refactored_module, True, "PASS")
    else:
        print(f"Behavior mismatch for {source_module}")
        log_result(source_module, refactored_module, False, "FAIL")
        all_tests_pass = False

summary = "\nAll SRC→REF tests passed." if all_tests_pass else "\nSome SRC→REF tests failed or were skipped. Check 'tests_result.txt' for details."
print(summary)
with open(RESULT_LOG, 'a', encoding='utf-8') as f:
    f.write("=" * 60 + "\n")
    f.write(summary + "\n")
