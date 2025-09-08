#!/usr/bin/env python3
"""Script to add @pytest.mark.asyncio decorators to all async test functions."""

import os
import re
from pathlib import Path

def fix_async_tests_in_file(file_path: Path) -> bool:
    """Fix async tests in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has async test functions
        if 'async def test_' not in content:
            return False
            
        # Check if pytest.mark.asyncio is already imported
        if '@pytest.mark.asyncio' in content:
            print(f"File {file_path} already has asyncio markers")
            return False
        
        lines = content.split('\n')
        new_lines = []
        modified = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this line defines an async test function
            if re.match(r'^(\s*)async def test_', line):
                # Get the indentation
                indent = re.match(r'^(\s*)', line).group(1)
                
                # Add the decorator before the function
                new_lines.append(f'{indent}@pytest.mark.asyncio')
                new_lines.append(line)
                modified = True
            else:
                new_lines.append(line)
            
            i += 1
        
        if modified:
            # Write the modified content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            print(f"Fixed async tests in {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix all test files."""
    test_directories = [
        Path('tests/unit'),
        Path('tests/integration'), 
        Path('tests/performance'),
        Path('tests/security'),
        Path('tests/compatibility')
    ]
    
    total_files = 0
    modified_files = 0
    
    for test_dir in test_directories:
        if not test_dir.exists():
            continue
            
        for test_file in test_dir.glob('test_*.py'):
            total_files += 1
            if fix_async_tests_in_file(test_file):
                modified_files += 1
    
    print(f"\nProcessed {total_files} test files")
    print(f"Modified {modified_files} files with async test fixes")

if __name__ == "__main__":
    main()