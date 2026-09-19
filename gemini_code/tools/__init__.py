"""
Tool registration module for Gemini Code agent.
"""

from .base import BaseTool, registry
from .file_tools import view_file, create_file, edit_file, delete_file
from .bash_tools import run_command
from .search_tools import glob_files, grep_search, list_dir
from .git_tools import git_status, git_diff, git_commit, git_undo

# Register file tools
registry.register(BaseTool(
    name="view_file",
    description="Read file content with line numbers. Specify start_line and end_line for slices.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute or relative path to file"},
            "start_line": {"type": "integer", "description": "Starting line number (1-based)"},
            "end_line": {"type": "integer", "description": "Ending line number (1-based)"},
        },
        "required": ["path"],
    },
    handler=view_file,
    is_dangerous=False,
))

registry.register(BaseTool(
    name="create_file",
    description="Create a new file or completely overwrite an existing one.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path of the file to create"},
            "content": {"type": "string", "description": "Full text content"},
            "overwrite": {"type": "boolean", "description": "Set to true to overwrite existing file"},
        },
        "required": ["path", "content"],
    },
    handler=create_file,
    is_dangerous=True,
))

registry.register(BaseTool(
    name="edit_file",
    description="Replace an exact, unique block of code in a file with new code, displaying a unified diff preview.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the target file"},
            "old_text": {"type": "string", "description": "Exact block of text to be replaced"},
            "new_text": {"type": "string", "description": "New replacement text"},
        },
        "required": ["path", "old_text", "new_text"],
    },
    handler=edit_file,
    is_dangerous=True,
))

registry.register(BaseTool(
    name="delete_file",
    description="Delete a file from the project filesystem.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path of the file to delete"},
        },
        "required": ["path"],
    },
    handler=delete_file,
    is_dangerous=True,
))

# Register command execution tool
registry.register(BaseTool(
    name="run_command",
    description="Execute a terminal command (PowerShell on Windows, Bash on Linux/macOS).",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The exact shell command line string to run"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default: 60)"},
        },
        "required": ["command"],
    },
    handler=run_command,
    is_dangerous=True,
))

# Register search tools
registry.register(BaseTool(
    name="glob_files",
    description="Find files matching wildcard glob pattern (e.g. '**/*.py', 'src/**/*.ts').",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern to search for"},
            "directory": {"type": "string", "description": "Directory to search within (default: .)"},
        },
        "required": ["pattern"],
    },
    handler=glob_files,
    is_dangerous=False,
))

registry.register(BaseTool(
    name="grep_search",
    description="Search for text or regular expression across project files.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search term or regex pattern"},
            "directory": {"type": "string", "description": "Base directory to search"},
            "is_regex": {"type": "boolean", "description": "Whether query is a regex pattern"},
        },
        "required": ["query"],
    },
    handler=grep_search,
    is_dangerous=False,
))

registry.register(BaseTool(
    name="list_dir",
    description="List contents of a directory with file sizes and directory indicators.",
    parameters={
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "Directory path to list"},
            "max_depth": {"type": "integer", "description": "Maximum recursive traversal depth"},
        },
    },
    handler=list_dir,
    is_dangerous=False,
))

# Register git tools
registry.register(BaseTool(
    name="git_status",
    description="Get short status of git repository.",
    parameters={"type": "object", "properties": {}},
    handler=git_status,
    is_dangerous=False,
))

registry.register(BaseTool(
    name="git_diff",
    description="Get uncommitted git diff.",
    parameters={
        "type": "object",
        "properties": {
            "cached": {"type": "boolean", "description": "Inspect staged changes if true"},
        },
    },
    handler=git_diff,
    is_dangerous=False,
))

registry.register(BaseTool(
    name="git_commit",
    description="Stage and commit changes with a conventional commit message.",
    parameters={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Commit message"},
        },
        "required": ["message"],
    },
    handler=git_commit,
    is_dangerous=True,
))

registry.register(BaseTool(
    name="git_undo",
    description="Revert unstaged file changes.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to revert (optional, all if omitted)"},
        },
    },
    handler=git_undo,
    is_dangerous=True,
))
