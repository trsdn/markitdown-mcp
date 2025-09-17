"""
This module contains REAL vulnerabilities and code quality issues
to test if our CI/CD system catches false negatives.

These are genuine problems that SHOULD be detected.
"""

import os
import subprocess
import pickle
import tempfile
from typing import Any


# SECURITY ISSUE 1: SQL Injection vulnerability
def unsafe_database_query(user_input: str) -> str:
    """Vulnerable to SQL injection attacks."""
    query = f"SELECT * FROM users WHERE name = '{user_input}'"  # SQL injection
    # This would execute: connection.execute(query)
    return query


# SECURITY ISSUE 2: Command injection vulnerability
def unsafe_system_command(filename: str) -> str:
    """Vulnerable to command injection."""
    command = f"cat {filename}"  # Command injection if filename is user-controlled
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout


# SECURITY ISSUE 3: Unsafe deserialization
def unsafe_pickle_load(data: bytes) -> Any:
    """Dangerous pickle deserialization - can execute arbitrary code."""
    return pickle.loads(data)  # Arbitrary code execution vulnerability


# SECURITY ISSUE 4: Path traversal vulnerability
def unsafe_file_access(user_path: str) -> str:
    """Vulnerable to path traversal attacks."""
    # No validation - user could pass "../../../etc/passwd"
    with open(user_path, 'r') as f:
        return f.read()


# SECURITY ISSUE 5: Hardcoded credentials
DATABASE_PASSWORD = "super_secret_admin_password_123"
API_SECRET_KEY = "sk-1a2b3c4d5e6f7g8h9i0j"
ENCRYPTION_KEY = "AES256-my-super-secret-encryption-key"


# CODE QUALITY ISSUE 1: Uninitialized variable usage
def broken_function(condition: bool) -> str:
    """This function has uninitialized variable usage."""
    if condition:
        result = "success"
    # Bug: result is not defined if condition is False
    return result  # UnboundLocalError when condition is False


# CODE QUALITY ISSUE 2: Infinite recursion
def infinite_recursion(n: int) -> int:
    """This function will cause stack overflow."""
    return infinite_recursion(n + 1)  # No base case!


# CODE QUALITY ISSUE 3: Division by zero
def unsafe_division(a: int, b: int) -> float:
    """No check for division by zero."""
    return a / b  # ZeroDivisionError when b = 0


# CODE QUALITY ISSUE 4: Memory leak potential
class LeakyClass:
    """This class has potential memory leaks."""
    def __init__(self):
        self.data = []
        self._circular_ref = self  # Circular reference

    def add_data(self, item):
        self.data.append(item)
        # Never clears data - potential memory leak


# CODE QUALITY ISSUE 5: Race condition
import threading

shared_counter = 0

def unsafe_counter_increment():
    """Race condition in shared variable access."""
    global shared_counter
    temp = shared_counter
    # Context switch could happen here!
    shared_counter = temp + 1  # Race condition


# CODE QUALITY ISSUE 6: Unreachable code
def unreachable_code_example():
    """Contains unreachable code."""
    return "early return"
    print("This line is never reached")  # Unreachable code
    x = 5 + 5  # Unreachable code


# PERFORMANCE ISSUE: Inefficient nested loops
def inefficient_algorithm(data_list):
    """O(n³) algorithm when O(n) would work."""
    result = []
    for i in range(len(data_list)):
        for j in range(len(data_list)):
            for k in range(len(data_list)):
                if data_list[i] == data_list[j] == data_list[k]:
                    result.append(data_list[i])
    return result