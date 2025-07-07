import os
import subprocess
import sys
import glob

def create_directories(*dirs):
    """Create directories if they don't exist."""
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def run_pynguin(project_path, output_path, module_name):
    """Run Pynguin to generate tests for a module."""
    create_directories(output_path, 'pynguin-report')
    cmd = f"pynguin --project-path {project_path} --output-path {output_path} --module-name {module_name} --maximum-iterations 10000 --algorithm WHOLE_SUITE --create-coverage-report -v"
    try:
        subprocess.run(cmd, shell=True, check=True)
    except Exception as e:
        print(f"Error: Pynguin failed to generate tests for {project_path}/{module_name}.py: {e}")
        print(f"Check pynguin-report logs for details. Stopping execution.")
        sys.exit(1)

def modify_imports(test_file, new_path, old_module, new_module):
    """Modify test file imports to point to the specified path and module."""
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
    """Run pytest on the test file."""
    try:
        result = subprocess.run(f"pytest {test_file} -v", shell=True, capture_output=True, text=True)
        print(result.stdout)
        return result.returncode == 0
    except Exception as e:

        print(f"Test execution failed for {test_file}: {e}")
        return False

def get_PYTHON_FILES(directory):
    """Get list of .py files in the directory, excluding __init__.py."""
    return [f for f in glob.glob(f"{directory}/*.py") if not f.endswith('__init__.py')]

def get_module_name(file_path):
    """Extract module name from file path (filename without .py)."""
    return os.path.splitext(os.path.basename(file_path))[0]

# Create necessary directories
create_directories('./tests/source_tests', './tests/refactored_tests', './pynguin-report')

# Define file mappings (source module -> refactored module)
file_mapping = {
    'test2': 'test2',
    'test1': 'test1'  # test1.py in source corresponds to test2.py in refactored
    # Add more mappings for other file pairs, e.g., 'file2': 'file2_refactored'
}

# Get Python files from both directories
source_files = get_PYTHON_FILES('./test/source')
refactored_files = get_PYTHON_FILES('./test/target')

# Generate tests for source files
for source_file in source_files:
    module_name = get_module_name(source_file)
    print(f"Generating tests for source module: {module_name}")
    run_pynguin('./test/source', './tests/source_tests', module_name)

# Generate tests for refactored files
for refactored_file in refactored_files:
    module_name = get_module_name(refactored_file)
    print(f"Generating tests for refactored module: {module_name}")
    run_pynguin('./test/refactored', './tests/refactored_tests', module_name)

# Cross-test
all_tests_pass = True
for source_file in source_files:
    source_module = get_module_name(source_file)
    refactored_module = file_mapping.get(source_module, source_module)
    test_file = f'./tests/source_tests/test_{source_module}.py'
    
    print(f"Cross-testing {source_module} tests against {refactored_module}")
    modify_imports(test_file, './test/refactored', source_module, refactored_module)
    if not run_tests(test_file):
        print(f"Source tests failed on refactored module {refactored_module}")
        all_tests_pass = False

for refactored_file in refactored_files:
    refactored_module = get_module_name(refactored_file)
    source_module = next((k for k, v in file_mapping.items() if v == refactored_module), refactored_module)
    test_file = f'./tests/refactored_tests/test_{refactored_module}.py'
    
    print(f"Cross-testing {refactored_module} tests against {source_module}")
    modify_imports(test_file, './test/source', refactored_module, source_module)
    if not run_tests(test_file):
        print(f"Refactored tests failed on source module {source_module}")
        all_tests_pass = False

# Final result
if all_tests_pass:
    print("Source and refactored code behave the same for tested scenarios.")
else:
    print("Behavioral differences detected. Check test failures.")