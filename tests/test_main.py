#!/usr/bin/env python3
"""Unit tests for the main methods."""

from typing import Any

from bytesight import print_bytecode


def test_example(capsys: Any) -> None:
    """Test printing some bytecode."""
    print_bytecode(lambda: None)
    expected = """\
//// Trace of `test_example.<locals>.<lambda>` :

// ========== test_main:11 `<lambda>` ==========
// >>> print_bytecode(lambda: None)
 11         0   LOAD_CONST           0   (None)
            2   RETURN_VALUE             ()
// =============================================

"""
    captured = capsys.readouterr()
    assert captured.out == expected
