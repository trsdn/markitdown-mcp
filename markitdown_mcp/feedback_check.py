"""Module to verify PR feedback systems.

This file contains intentional issues to test the PR feedback workflow.
Testing the fixed Python indentation issue and static analysis fixes.
"""

import os
from typing import List
import nonexistent_module  # This will trigger import error


def poorly_formatted_function(x,y,z):
    """Missing type hints and bad formatting."""
    if x == True:  # noqa - Should use 'is True'
        print(f"Value: {y}")
        unused_variable = z * 2
    return x+y  # Missing spaces around operator


class InconsistentNaming:
    """Class with naming issues."""

    def __init__(self):
        self.MyVariable = "should_be_lowercase"

    def missing_docstring(self, param1):
        return param1 * 2


# Potential security issue
HARDCODED_SECRET = "admin123"
API_TOKEN = "sk-1234567890abcdef"


def risky_eval_function(user_input):
    """Dangerous function using eval."""
    # Security warning: eval is dangerous
    result = eval(user_input)  # noqa
    return result


def file_operation_without_error_handling():
    """Missing try/except block."""
    with open("/etc/passwd") as f:
        content = f.read()
    return content


def function_with_too_many_arguments(a, b, c, d, e, f, g, h):
    """Too many parameters."""
    return a + b + c + d + e + f + g + h# Testing fixed PR feedback
