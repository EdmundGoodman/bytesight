#!/usr/bin/env python3
"""Data structures representing trace events."""

import abc
import dis
import inspect
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


USE_ADAPTIVE: bool = False


@dataclass(eq=True, frozen=True)
class StopEvent:
    """An event guarding the end of the trace."""

    exception: Exception | None


@dataclass(eq=True, frozen=True)
class TracedEvent(abc.ABC):
    """An event in a trace, having both a current and previous timestamp."""

    @classmethod
    @abc.abstractmethod
    def from_frame(
        cls,
        frame: types.FrameType,
        arg: Any,
    ) -> "TracedEvent": ...


@dataclass(eq=True, frozen=True)
class CallEvent(TracedEvent):
    """A call event in a trace."""

    name: str
    file: Path
    lineno: int | None

    @classmethod
    def get_name(cls, frame: types.FrameType) -> str:
        """Get the name of a function."""
        if sys.version_info.minor <= 10:
            return frame.f_code.co_name
        return frame.f_code.co_qualname

    @classmethod
    def from_frame(
        cls,
        frame: types.FrameType,
        arg: None,
    ) -> "CallEvent":
        """Construct the representation from a frame object."""
        return cls(
            name=cls.get_name(frame),
            file=Path(frame.f_code.co_filename),
            lineno=frame.f_code.co_firstlineno,
        )


@dataclass(eq=True, frozen=True)
class LineEvent(TracedEvent):
    """A call event in a trace."""

    contents: str

    @classmethod
    def from_frame(
        cls,
        frame: types.FrameType,
        arg: None,
    ) -> "LineEvent":
        """Construct the representation from a frame object."""
        try:
            frameinfo = inspect.getframeinfo(frame)
            code_context = frameinfo.code_context
            assert code_context is not None
            contents = code_context[0].strip()
        except Exception:
            contents = "<source not available>"

        return cls(
            contents=contents,
        )


@dataclass(eq=True, frozen=True)
class ReturnEvent(TracedEvent):
    """A call event in a trace."""

    return_value: Any

    @classmethod
    def from_frame(
        cls,
        frame: types.FrameType,
        arg: None,
    ) -> "ReturnEvent":
        """Construct the representation from a frame object."""
        return cls(return_value=arg)


@dataclass(eq=True, frozen=True)
class ExceptionEvent(TracedEvent):
    """A call event in a trace."""

    exception: type
    value: Exception = field(compare=False)
    traceback: types.TracebackType | None = field(compare=False)

    @classmethod
    def from_frame(
        cls,
        frame: types.FrameType,
        arg: tuple[type, Exception, types.TracebackType | None],
    ) -> "ExceptionEvent":
        """Construct the representation from a frame object."""
        return cls(
            exception=arg[0],
            value=arg[1],
            traceback=arg[2],
        )


@dataclass(eq=True, frozen=True)
class OpcodeEvent(TracedEvent):
    """A call event in a trace."""

    lineno: int | None
    curr_instr: bool
    jump: bool
    offset: int
    opname: str
    arg: int | None
    argrepr: str

    @classmethod
    def get_opcode(cls, frame: types.FrameType) -> dis.Instruction | None:
        """Get the current opcode name for a frame.

        This can be found by retrieving the instruction at the correct offset in
        the frame.
        """
        if sys.version_info.minor >= 11:
            instructions = dis.get_instructions(frame.f_code, adaptive=USE_ADAPTIVE)
        else:
            instructions = dis.get_instructions(frame.f_code)
        for instr in instructions:
            if instr.offset == frame.f_lasti:
                return instr
        return None

    @classmethod
    def get_lineno(cls, instruction: dis.Instruction) -> int | None:
        """Get the line number for an instruction."""
        if sys.version_info.minor <= 11:
            return instruction.starts_line
        if instruction.line_number is not None:
            return instruction.line_number
        return getattr(instruction.positions, "lineno", None)

    @classmethod
    def from_frame(
        cls,
        frame: types.FrameType,
        arg: None,
    ) -> "OpcodeEvent":
        """Construct the representation from a frame object."""
        instruction = cls.get_opcode(frame)
        assert instruction is not None

        # TODO: `OpcodeEvent` could just store the instruction and make these properties?
        return cls(
            lineno=cls.get_lineno(instruction),
            curr_instr=False,
            jump=instruction.is_jump_target,
            offset=instruction.offset,
            opname=instruction.opname,
            arg=instruction.arg,
            argrepr=instruction.argrepr,
        )


EVENT_NAME_LOOKUP: dict[str, type[TracedEvent]] = {
    "call": CallEvent,
    "line": LineEvent,
    "return": ReturnEvent,
    "exception": ExceptionEvent,
    "opcode": OpcodeEvent,
}
