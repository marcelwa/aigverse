"""Exceptions raised by the ABC bridge."""

from __future__ import annotations

__all__ = [
    "AbcError",
    "AbcExecutionError",
    "AbcNotFoundError",
    "AbcTimeoutError",
]

_OUTPUT_LIMIT = 4000


def _truncate(output: str) -> str:
    """Shortens captured ABC output for inclusion in an error message.

    Args:
        output: The captured ABC output.

    Returns:
        The output, truncated to a readable length with an explicit marker.
    """
    stripped = output.strip()
    if len(stripped) <= _OUTPUT_LIMIT:
        return stripped
    return stripped[:_OUTPUT_LIMIT] + "\n... (output truncated)"


class AbcError(RuntimeError):
    """Base class for every failure raised by the ABC bridge."""


class AbcNotFoundError(AbcError):
    """Raised when no usable ABC executable could be located."""


class AbcExecutionError(AbcError):
    """Raised when ABC ran but did not produce a usable result.

    ABC exits with status 0 even for unknown commands and unreadable files, and
    writes everything to standard output, so the captured output is the only
    diagnostic available and is attached here.

    Attributes:
        binary: The ABC executable that was invoked.
        command: The command string that was passed to ABC.
        output: The output captured from ABC, truncated if very long.
    """

    def __init__(self, message: str, *, binary: str, command: str, output: str) -> None:
        """Initializes the error.

        Args:
            message: A short description of what went wrong.
            binary: The ABC executable that was invoked.
            command: The command string that was passed to ABC.
            output: The output captured from ABC.
        """
        self.binary = binary
        self.command = command
        self.output = _truncate(output)

        details = f"{message}\n  binary:  {binary}\n  command: {command}"
        if self.output:
            details += f"\n  output:\n{self.output}"
        super().__init__(details)


class AbcTimeoutError(AbcExecutionError):
    """Raised when ABC did not terminate within the requested timeout."""
