---
description: Perform a deep architectural and security review of specific files.
argument-hint: [file_path]
allowed-tools: [Read, Grep, Glob]
---

## Task
Perform a comprehensive review of the following code: $ARGUMENTS

## Review Checklist
1. **Security**: Identify potential vulnerabilities or unsafe patterns.
2. **Architecture**: Evaluate if the code follows existing project conventions.
3. **Performance**: Suggest optimizations for loops or heavy operations.

## Output Format
Provide a summary of findings followed by a Markdown table of suggested changes.