#!/usr/bin/env python3
"""
Script to modernize Python typing annotations to Python 3.10+ syntax.

Replacements:
- Optional[X] → X | None
- List[X] → list[X]
- Dict[K, V] → dict[K, V]
- Set[X] → set[X]
- Tuple[X, Y] → tuple[X, Y]
- Union[X, Y] → X | Y
"""

import re
import sys
from pathlib import Path


# Types that should be replaced with native equivalents
REPLACEABLE_TYPES = {"Optional", "List", "Dict", "Set", "Tuple", "Union"}

# Types that should remain from typing module
KEEP_TYPES = {
    "Generic",
    "TypeVar",
    "Protocol",
    "runtime_checkable",
    "Annotated",
    "AsyncGenerator",
    "Generator",
    "Type",
    "Callable",
    "Any",
    "ClassVar",
    "Literal",
    "Final",
    "TypeAlias",
    "Awaitable",
    "Coroutine",
    "AsyncIterator",
    "Iterator",
    "Iterable",
    "Sequence",
    "Mapping",
    "MutableMapping",
    "AbstractSet",
    "MutableSet",
    "Deque",
    "DefaultDict",
    "OrderedDict",
    "Counter",
    "ChainMap",
    "cast",
    "overload",
    "TypedDict",
    "NamedTuple",
}


def find_matching_bracket(text: str, start_pos: int) -> int:
    """Find the matching closing bracket for an opening bracket at start_pos."""
    count = 1
    pos = start_pos + 1
    while pos < len(text) and count > 0:
        if text[pos] == "[":
            count += 1
        elif text[pos] == "]":
            count -= 1
        pos += 1
    return pos - 1 if count == 0 else -1


def replace_optional(content: str) -> str:
    """Replace Optional[X] with X | None."""
    result = []
    i = 0
    while i < len(content):
        # Look for Optional[
        if content[i : i + 9] == "Optional[":
            # Find the matching closing bracket
            close_pos = find_matching_bracket(content, i + 8)
            if close_pos != -1:
                inner_type = content[i + 9 : close_pos]
                result.append(f"{inner_type} | None")
                i = close_pos + 1
                continue
        result.append(content[i])
        i += 1
    return "".join(result)


def replace_union(content: str) -> str:
    """Replace Union[X, Y, ...] with X | Y | ...."""
    result = []
    i = 0
    while i < len(content):
        # Look for Union[
        if content[i : i + 6] == "Union[":
            # Find the matching closing bracket
            close_pos = find_matching_bracket(content, i + 5)
            if close_pos != -1:
                inner_types = content[i + 6 : close_pos]
                # Split by comma but respect nested brackets
                types_list = split_respecting_brackets(inner_types)
                result.append(" | ".join(t.strip() for t in types_list))
                i = close_pos + 1
                continue
        result.append(content[i])
        i += 1
    return "".join(result)


def split_respecting_brackets(text: str) -> list[str]:
    """Split text by commas, but respect brackets."""
    parts = []
    current = []
    bracket_depth = 0

    for char in text:
        if char == "[":
            bracket_depth += 1
            current.append(char)
        elif char == "]":
            bracket_depth -= 1
            current.append(char)
        elif char == "," and bracket_depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)

    if current:
        parts.append("".join(current))

    return parts


def replace_generic_type(content: str, old_name: str, new_name: str) -> str:
    """Replace GenericType[X] with generictype[X]."""
    pattern = rf"\b{old_name}\["
    return re.sub(pattern, f"{new_name}[", content)


def update_imports(content: str) -> str:
    """Update typing imports to remove replaced types."""
    lines = content.split("\n")
    new_lines = []

    for line in lines:
        # Check if this is a typing import line
        if re.match(r"^from typing import ", line):
            # Extract imported items
            import_match = re.match(r"^from typing import (.+)$", line)
            if import_match:
                imports_str = import_match.group(1)

                # Handle multiline imports (ending with parenthesis or continuation)
                if "(" in imports_str or "\\" in line:
                    # For now, keep the line as-is if it's multiline
                    # (we'll handle simple cases first)
                    new_lines.append(line)
                    continue

                # Split imports
                imports = [imp.strip() for imp in imports_str.split(",")]

                # Filter out replaced types
                remaining_imports = [
                    imp for imp in imports if imp.split()[0] not in REPLACEABLE_TYPES
                ]

                # If no imports remain, skip this line
                if not remaining_imports:
                    continue

                # Reconstruct import line
                new_line = f"from typing import {', '.join(remaining_imports)}"
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def modernize_file(file_path: Path) -> bool:
    """Modernize a single Python file. Returns True if changes were made."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Step 1: Replace Optional[X] with X | None
        content = replace_optional(content)

        # Step 2: Replace Union[X, Y] with X | Y
        content = replace_union(content)

        # Step 3: Replace List[X] with list[X]
        content = replace_generic_type(content, "List", "list")

        # Step 4: Replace Dict[K, V] with dict[K, V]
        content = replace_generic_type(content, "Dict", "dict")

        # Step 5: Replace Set[X] with set[X]
        content = replace_generic_type(content, "Set", "set")

        # Step 6: Replace Tuple[X, Y] with tuple[X, Y]
        content = replace_generic_type(content, "Tuple", "tuple")

        # Step 7: Update imports
        content = update_imports(content)

        # Write back if changes were made
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    # Get project root
    project_root = Path(__file__).parent.parent

    # Directories to process
    dirs_to_process = [
        project_root / "app",
        project_root / "tests",
    ]

    # Find all Python files
    python_files = []
    for directory in dirs_to_process:
        if directory.exists():
            python_files.extend(directory.rglob("*.py"))

    # Process each file
    modified_count = 0
    for file_path in python_files:
        # Skip __pycache__ and virtual environment directories
        if "__pycache__" in str(file_path) or "/.venv/" in str(file_path):
            continue

        if modernize_file(file_path):
            print(f"✓ Modified: {file_path.relative_to(project_root)}")
            modified_count += 1

    print(f"\n✓ Modernization complete! Modified {modified_count} files.")


if __name__ == "__main__":
    main()
