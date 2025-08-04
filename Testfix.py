import os
import subprocess
import sys
import glob
import ast
import re

RESULT_LOG = "tests_result.txt"

# Unchanged functions: log_result, has_func_or_class, make_dirs, run_pynguin, clean_test_file, run_tests
# Including only modified or critical sections

def validate_module_name(module_name):
    """Check if the module name is valid for Python import."""
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', module_name))

def modify_imports(test_file, new_path, old_module, new_module, subfolder=None):
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

        # Validate module and subfolder names
        if subfolder and not validate_module_name(subfolder):
            print(f"Error: Invalid subfolder name {subfolder} for import. Skipping.")
            return False
        if not validate_module_name(new_module):
            print(f"Error: Invalid module name {new_module} for import. Skipping.")
            return False

        formatted_path = new_path.replace('\\\\', '/').replace('C:', 'C:/')
        new_lines.insert(0, f"import sys\n")
        new_lines.insert(1, f'sys.path.insert(0, "{formatted_path}")\n')
        insert_idx = 2
        for alias_num in sorted(used_aliases):
            if subfolder:
                # Import with subfolder: e.g., import user.pip_no_1_user as module_0
                new_lines.insert(insert_idx, f"import {subfolder}.{new_module} as module_{alias_num}\n")
            else:
                new_lines.insert(insert_idx, f"import {new_module} as module_{alias_num}\n")
            insert_idx += 1
        if not has_pytest:
            new_lines.insert(insert_idx, "import pytest\n")

        with open(test_file, 'w') as f:
            f.writelines(new_lines)

        print(f"Modified imports in {test_file} to use {subfolder}.{new_module if subfolder else new_module} from {new_path}")
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

def get_files(directory):
    """Get all .py files in directory and its subfolders."""
    try:
        return [f for f in glob.glob(os.path.join(os.path.abspath(directory), "**/*.py"), recursive=True)]
    except Exception as e:
        print(f"Error accessing directory {directory}: {e}")
        return []

def get_mod_name(file_path, is_refactored=False):
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    if is_refactored:
        # Handle pip_no_X_ prefix specifically
        match = re.match(r'pip_no_\d+_(.*)', base_name)
        return match.group(1) if match else base_name
    return base_name

def get_refactored_filename(file_path):
    """Return the full filename of the refactored file."""
    return os.path.splitext(os.path.basename(file_path))[0]

def get_refactored_subfolder(file_path):
    """Return the subfolder name for a refactored file."""
    parent_dir = os.path.basename(os.path.dirname(file_path))
    return parent_dir if parent_dir != os.path.basename(os.path.dirname(os.path.dirname(file_path))) else None

# Initialize log file
with open(RESULT_LOG, 'w', encoding='utf-8') as f:
    f.write("Test Results Log\n")
    f.write("=" * 60 + "\n")

# Define directories
source_dir = os.path.expanduser("~/Desktop/pqc/refactor/input/cryptome/excuted")
refactored_dir = os.path.expanduser("~/Desktop/pqc/refactor/output/cryptodoke/excuted")
make_dirs(source_dir, refactored_dir, './tests/source_tests', './pynguin-report')

# Verify directories
if not os.path.exists(source_dir):
    print(f"Error: Source directory {source_dir} does not exist.")
    with open(RESULT_LOG, 'a', encoding='utf-8') as f:
        f.write(f"Error: Source directory {source_dir} does not exist.\n")
    sys.exit(1)
if not os.path.exists(refactored_dir):
    print(f"Error: Refactored directory {refactored_dir} does not exist.")
    with open(RESULT_LOG, 'a', encoding='utf-8') as f:
        f.write(f"Error: Refactored directory {refactored_dir} does not exist.\n")
    sys.exit(1)

# Get source and refactored files
source_files = get_files(source_dir)
refactored_files = get_files(refactored_dir)

if not source_files:
    print(f"No Python files found in source directory {source_dir}.")
    with open(RESULT_LOG, 'a', encoding='utf-8') as f:
        f.write(f"No Python files found in source directory {source_dir}.\n")
    sys.exit(1)
if not refactored_files:
    print(f"No Python files found in refactored directory {refactored_dir}.")
    with open(RESULT_LOG, 'a', encoding='utf-8') as f:
        f.write(f"No Python files found in refactored directory {refactored_dir}.\n")
    sys.exit(1)

# Create mapping between source and refactored modules
source_module_names = {get_mod_name(f) for f in source_files}
file_mapping = {}
for source_name in source_module_names:
    # Look for refactored files in a subfolder named after the source file
    subfolder_path = os.path.join(refactored_dir, source_name)
    if os.path.exists(subfolder_path):
        subfolder_files = get_files(subfolder_path)
        refactored_modules = [
            get_refactored_filename(f) for f in subfolder_files
            if get_mod_name(f, is_refactored=True) == source_name
        ]
        if refactored_modules:
            file_mapping[source_name] = [(source_name, mod) for mod in refactored_modules]

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
    refactored_modules = file_mapping.get(source_module, [])

    if not refactored_modules:
        print(f"No matching refactored module for {source_module}. Skipping.")
        log_result(source_module, "None", False, "FAIL (No Matching Refactored Module)")
        all_tests_pass = False
        continue

    test_file = os.path.join('./tests/source_tests', f"test_{source_module}.py")
    print(f"\n=== Testing {source_module} against refactored modules ===")

    if not os.path.exists(test_file):
        print(f"Test file {test_file} not found. Skipping.")
        log_result(source_module, "None", False, "FAIL (Missing Test)")
        all_tests_pass = False
        continue

    # Test each refactored module
    for subfolder, refactored_module in refactored_modules:
        refactored_file = os.path.join(refactored_dir, subfolder, f"{refactored_module}.py")
        if not os.path.exists(refactored_file):
            print(f"Refactored module {refactored_file} not found. Skipping.")
            log_result(source_module, f"{subfolder}.{refactored_module}", False, "FAIL (Missing Refactored Module)")
            all_tests_pass = False
            continue

        if not validate_module_name(subfolder) or not validate_module_name(refactored_module):
            print(f"Error: Invalid module name {subfolder}.{refactored_module} for import. Skipping.")
            log_result(source_module, f"{subfolder}.{refactored_module}", False, "FAIL (Invalid Module Name)")
            all_tests_pass = False
            continue

        print(f"Running tests on refactored: {subfolder}.{refactored_module}")
        if not modify_imports(test_file, refactored_dir, source_module, refactored_module, subfolder=subfolder):
            log_result(source_module, f"{subfolder}.{refactored_module}", False, "FAIL (Import Modification)")
            all_tests_pass = False
            continue
        refactored_result = run_tests(test_file)

        if refactored_result:
            print(f"Behavior matches expected (source-derived) for {source_module} against {subfolder}.{refactored_module}")
            log_result(source_module, f"{subfolder}.{refactored_module}", True, "PASS")
        else:
            print(f"Behavior mismatch for {source_module} against {subfolder}.{refactored_module}")
            log_result(source_module, f"{subfolder}.{refactored_module}", False, "FAIL")
            all_tests_pass = False

summary = "\nAll SRC→REF tests passed." if all_tests_pass else "\nSome SRC→REF tests failed or were skipped. Check 'tests_result.txt' for details."
print(summary)
with open(RESULT_LOG, 'a', encoding='utf-8') as f:
    f.write("=" * 60 + "\n")
    f.write(summary + "\n")
