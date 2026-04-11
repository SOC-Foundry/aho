#!/usr/bin/env fish
# test_aho_mcp_cli_e2e.fish — End-to-end CLI test for bin/aho-mcp
# 0.2.4 W2 — catches the empty-list and empty-parens regressions from 0.2.3.

set -l test_pass 0
set -l test_fail 0
set -l project_root (git rev-parse --show-toplevel 2>/dev/null; or echo (pwd))

# --- Test 1: bin/aho-mcp list exits 0 ---
set -l output ($project_root/bin/aho-mcp list 2>&1)
if test $status -eq 0
    set test_pass (math $test_pass + 1)
    echo "PASS: bin/aho-mcp list exits 0"
else
    set test_fail (math $test_fail + 1)
    echo "FAIL: bin/aho-mcp list exited non-zero"
end

# --- Test 2: header contains version in parens (not empty parens) ---
if string match -q '*MCP Server Fleet (0.2.4)*' -- $output
    set test_pass (math $test_pass + 1)
    echo "PASS: header contains 'MCP Server Fleet (0.2.4)'"
else
    set test_fail (math $test_fail + 1)
    echo "FAIL: header missing version — got:"
    echo $output[1]
end

# --- Test 3: row count for [ok]/[--] equals 9 ---
set -l row_count (string match -r '\[(ok|--)\]' -- $output | wc -l)
# Each match produces 2 lines (full match + group), so divide by 2
set row_count (math $row_count / 2)
if test $row_count -eq 9
    set test_pass (math $test_pass + 1)
    echo "PASS: 9 package rows found"
else
    set test_fail (math $test_fail + 1)
    echo "FAIL: expected 9 package rows, got $row_count"
end

# --- Summary ---
echo "---"
echo "Results: $test_pass passed, $test_fail failed"
if test $test_fail -gt 0
    exit 1
end
exit 0
