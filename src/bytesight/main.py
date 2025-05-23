#!/usr/bin/env python3
"""Bytesight tracing profiler for Python bytecode."""

from collections.abc import Callable
from time import perf_counter
from typing import Any

from bytesight.profiler import BytecodeProfiler


def print_bytecode(
    func: Callable[[], Any],
    *args: list[Any],
    **kwargs: dict[str, Any],
) -> None:
    """Print the bytecode executed when running a function.

    The function must be pure, as it is run many times to get various peices of
    data.
    """
    profiler = BytecodeProfiler(num_warmups=0, num_repeats=0)
    profiler.profile(func, *args, **kwargs)
    BytecodeProfiler.print_events(
        events=profiler.events,
        trace_name=func.__qualname__,
        elapsed_times=None,
    )


def profile_bytecode(
    func: Callable[[], Any],
    *args: list[Any],
    **kwargs: dict[str, Any],
) -> None:
    """Profile the bytecode executed when running a function.

    The function must be pure, as it is run many times to get various peices of
    data.
    """
    profiler = BytecodeProfiler()
    profiler.profile(func, *args, **kwargs)
    elapsed_times = profiler.calculate_trace_times()

    BytecodeProfiler.print_events(
        events=profiler.events,
        trace_name=func.__qualname__,
        elapsed_times=elapsed_times,
    )


def main() -> None:  # pragma: no cover
    """Say hello."""

    def inner_function(x: int | str | float):
        assert x

    def raise_exception():
        raise ValueError("Help")

    def example_function():
        inner_function(1)
        inner_function("Hello")
        _x = perf_counter()
        raise_exception()
        inner_function(5.0)

    nop_sled = BytecodeProfiler.get_nop_sled(50)

    def go():
        example_function()

    profile_bytecode(go)
    # print_bytecode(go)


if __name__ == "__main__":
    main()
