#!/usr/bin/env python3
"""Guard for /ask: blocks every action that could modify something while the
user's latest message is an /ask invocation (plain `/ask` or `/<plugin>:ask`).

PreToolUse hook. Reads the event from stdin. Exit 2 = block (reason on stderr),
exit 0 = no decision (normal permission flow continues).

Policy: allowlist. Anything not recognized as read-only is blocked.
"""
import json
import os
import re
import shlex
import sys

ASK_MARKER = re.compile(r"<command-name>/(?:[\w.-]+:)?ask</command-name>")
TRANSCRIPT_TAIL_BYTES = 4 * 1024 * 1024

READ_ONLY_TOOLS = {
    "Read", "Grep", "Glob", "LS", "WebFetch", "WebSearch", "ToolSearch",
    "AskUserQuestion", "Skill", "LSP", "ListMcpResourcesTool",
    "ReadMcpResourceTool", "ReadMcpResourceDirTool",
}

READ_ONLY_COMMANDS = {
    "ls", "cat", "head", "tail", "less", "wc", "grep", "egrep", "fgrep", "rg",
    "fd", "find", "file", "stat", "du", "df", "pwd", "echo", "printf", "which",
    "type", "tree", "sort", "uniq", "cut", "tr", "awk", "jq", "yq", "diff",
    "cmp", "date", "env", "printenv", "basename", "dirname", "realpath",
    "readlink", "column", "nl", "sed", "cd", "true", "test", "[",
}
GIT_READ_SUBCOMMANDS = {
    "status", "log", "diff", "show", "blame", "grep", "ls-files", "ls-tree",
    "rev-parse", "describe", "shortlog", "reflog", "cat-file", "merge-base",
    "rev-list", "branch", "remote", "tag", "config", "stash",
}
FIND_WRITE_FLAGS = {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprintf", "-fls"}
SEPARATORS = {"|", "||", "&&", ";", "&", "(", ")", "\n"}
SAFE_REDIRECT_TARGETS = {"/dev/null"}

MCP_READ_VERBS = {
    "get", "list", "search", "read", "query", "fetch", "find", "lookup", "view",
    "whoami", "resolve", "describe", "retrieve", "count", "docs", "overview",
    "diagnostics", "instructions",
}
MCP_WRITE_VERBS = {
    "create", "update", "delete", "send", "add", "remove", "set", "edit", "write",
    "insert", "replace", "rename", "upload", "publish", "post", "apply", "mark",
    "unmark", "trash", "untrash", "label", "unlabel", "share", "copy", "move",
    "transition", "schedule", "complete", "authenticate", "store", "activate",
    "onboarding", "sync", "put", "generate", "run", "cancel", "respond", "forward",
    "reply", "draft", "duplicate", "merge", "safe", "insert", "open", "use",
}
SQL_READ_START = re.compile(r"^\s*(select|show|describe|desc|explain|with)\b", re.IGNORECASE)
SQL_WRITE_WORD = re.compile(
    r"\b(insert|update|delete|replace|merge|drop|alter|create|truncate|grant|revoke|"
    r"rename|call|lock|set|load|handler|do)\b|\binto\s+outfile\b",
    re.IGNORECASE,
)


def last_user_prompt(transcript_path):
    """Text of the latest real user message (skips tool results, meta entries and notifications)."""
    with open(transcript_path, "rb") as transcript_file:
        transcript_file.seek(0, os.SEEK_END)
        size_bytes = transcript_file.tell()
        transcript_file.seek(max(0, size_bytes - TRANSCRIPT_TAIL_BYTES))
        lines = transcript_file.read().decode("utf-8", errors="replace").splitlines()
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get("type") != "user" or entry.get("isMeta"):
            continue
        content = entry.get("message", {}).get("content")
        if isinstance(content, list):
            if any(block.get("type") == "tool_result" for block in content if isinstance(block, dict)):
                continue
            content = " ".join(
                block.get("text", "") for block in content if isinstance(block, dict)
            )
        if not isinstance(content, str):
            continue
        if content.lstrip().startswith("<task-notification>"):
            continue
        return content
    return ""


def split_name_words(tool_name):
    action = tool_name.split("__")[-1]
    action = re.sub(r"([a-z])([A-Z])", r"\1_\2", action)
    return {word.lower() for word in re.split(r"[_\-]", action) if word}


def check_sql(tool_input):
    sql_text = tool_input.get("sql") or tool_input.get("query") or ""
    statements = [statement for statement in sql_text.split(";") if statement.strip()]
    if len(statements) != 1:
        return "only a single read-only SQL statement is allowed"
    if not SQL_READ_START.match(statements[0]) or SQL_WRITE_WORD.search(statements[0]):
        return "only SELECT / SHOW / DESCRIBE / EXPLAIN"
    return None


def check_mcp(tool_name, tool_input):
    words = split_name_words(tool_name)
    if "mysql" in tool_name.lower() or "sql" in words:
        return check_sql(tool_input)
    if words & MCP_WRITE_VERBS or not words & MCP_READ_VERBS:
        return f"tool {tool_name} is not read-only"
    return None


def check_segment(words):
    if not words:
        return None
    if words[0] == "rtk":
        words = words[1:]
    while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
        words = words[1:]
    if not words:
        return None
    command = os.path.basename(words[0])
    arguments = words[1:]
    if command == "git":
        while arguments and arguments[0].startswith("-"):
            takes_value = arguments[0] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace")
            arguments = arguments[2:] if takes_value else arguments[1:]
        subcommand = arguments[0] if arguments else ""
        if subcommand not in GIT_READ_SUBCOMMANDS:
            return f"git {subcommand} modifies the repository"
        if subcommand == "branch" and any(arg in arguments for arg in ("-d", "-D", "-m", "-M", "-c", "-C", "--delete", "--move", "--copy", "-f", "--force")):
            return "git branch with write flags"
        if subcommand == "stash" and arguments[arguments.index("stash") + 1:][:1] not in (["list"], ["show"]):
            return "git stash only with list / show"
        if subcommand == "config" and not any(arg in arguments for arg in ("--get", "--get-all", "--list", "-l", "--get-regexp")):
            return "git config only with --get / --list"
        positional_after = [arg for arg in arguments[arguments.index(subcommand) + 1:] if not arg.startswith("-")]
        if subcommand == "tag" and positional_after and not {"-l", "--list"} & set(arguments):
            return "git tag only for listing"
        if subcommand == "remote" and positional_after[:1] not in ([], ["show"], ["get-url"]):
            return "git remote only for listing"
        return None
    if command == "gh" and arguments[:2] in (["pr", "view"], ["pr", "list"], ["pr", "diff"], ["pr", "checks"], ["issue", "view"], ["issue", "list"], ["run", "view"], ["run", "list"]):
        return None
    if command not in READ_ONLY_COMMANDS:
        return f"command {command} is not on the read-only allowlist"
    if command == "sed" and any(arg.startswith("-i") or arg == "--in-place" for arg in arguments):
        return "sed -i modifies files"
    if command == "find" and FIND_WRITE_FLAGS & set(arguments):
        return "find with -delete / -exec"
    if command == "awk" and any("system(" in arg or "print >" in arg or "printf >" in arg for arg in arguments):
        return "awk with file output or system()"
    return None


def check_bash(command_text):
    if "`" in command_text or "$(" in command_text or "<(" in command_text or ">(" in command_text:
        return "command substitution is not allowed in /ask"
    lexer = shlex.shlex(command_text, posix=True, punctuation_chars=";&|()<>")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return "could not parse the command"
    segment = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in SEPARATORS:
            problem = check_segment(segment)
            if problem:
                return problem
            segment = []
        elif ">" in token:
            target = tokens[index + 1] if index + 1 < len(tokens) else ""
            if token.endswith("&") and target.isdigit():
                index += 2
                continue
            if target not in SAFE_REDIRECT_TARGETS:
                return "redirecting output to a file is not allowed"
            index += 2
            continue
        elif token in ("<", "<<", "<<<"):
            segment.append(token)
        else:
            if token.isdigit() and index + 1 < len(tokens) and ">" in tokens[index + 1]:
                index += 1
                continue
            segment.append(token)
        index += 1
    return check_segment(segment)


def decide(tool_name, tool_input):
    if tool_name in READ_ONLY_TOOLS:
        return None
    if tool_name == "Bash":
        return check_bash(tool_input.get("command", ""))
    if tool_name.startswith("mcp__"):
        return check_mcp(tool_name, tool_input)
    return f"{tool_name} is not read-only"


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    try:
        ask_active = bool(ASK_MARKER.search(last_user_prompt(event.get("transcript_path", ""))))
    except OSError:
        return 0
    if not ask_active:
        return 0
    try:
        problem = decide(event.get("tool_name", ""), event.get("tool_input") or {})
    except Exception as error:  # in /ask mode, block when in doubt
        problem = f"guard error ({error})"
    if problem:
        print(f"/ask is read-only: {problem}. Answer with what you can read, or "
              "describe the action so the user can request it outside /ask.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
