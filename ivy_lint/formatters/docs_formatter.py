import re
import ast

from ivy_lint.formatters import BaseFormatter


def format_docstring(doc):
    """Formats a single docstring."""
    # Rename "Functional Examples" to "Examples" and remove old underline
    doc = re.sub(r'(\s*)Functional Examples\s*\n-*', r'\1Examples\n\1--------', doc)
    
    # Remove any extra underline if it happens to appear after "Examples"
    doc = re.sub(r'Examples\n--------\s*-*', 'Examples\n--------', doc)
    
    # Ensure there's an empty line before the "Examples" header if it's preceded by another section
    doc = re.sub(r'([^\n])\n(\s*)Examples\n\2--------', r'\1\n\n\2Examples\n\2--------', doc)
    
    # Identify code blocks
    lines = doc.split('\n')
    is_codeblock = False
    codeblock_start_lines = set()  # This will store indices of lines which start a code block

    for idx, line in enumerate(lines):
        stripped_line = line.strip()

        if not is_codeblock and stripped_line.startswith('>>>'):
            is_codeblock = True
            codeblock_start_lines.add(idx)
        elif is_codeblock and (not stripped_line or not stripped_line.startswith(('>>>', '...'))):
            is_codeblock = False
    
    # Add blank lines before code blocks
    formatted_lines = []
    for idx, line in enumerate(lines):
        if idx in codeblock_start_lines and formatted_lines and formatted_lines[-1].strip():  # Insert blank line before code block
            formatted_lines.append('')
        formatted_lines.append(line)
            
    return '\n'.join(formatted_lines)

def format_all_docstrings(python_code):
    """Extracts all docstrings from the given Python code, formats them, and replaces the original ones with the formatted versions."""
    tree = ast.parse(python_code)
    replacements = {}

    # Extract all docstrings from the AST tree
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.AsyncFor)):
            original_docstring = ast.get_docstring(node, clean=False)
            if original_docstring:
                formatted_docstring = format_docstring(original_docstring)
                if original_docstring != formatted_docstring:  # Only add if there are changes
                    replacements[original_docstring] = formatted_docstring

    # Replace the docstrings safely
    for original, formatted in replacements.items():
        python_code = python_code.replace(original, formatted, 1)  # Only replace once to be safe
    
    return python_code

class DocstringFormatter(BaseFormatter):
    def _format_file(self, filename: str) -> bool:
        with open(filename, 'r') as file:
            original_content = file.read()

        formatted_content = format_all_docstrings(original_content)

        if original_content != formatted_content:
            with open(filename, 'w') as file:
                file.write(formatted_content)
            return True

        return False