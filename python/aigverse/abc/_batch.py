"""Parallel execution of one ABC script over many networks."""

from __future__ import annotations

import os
import sys
from concurrent.futures import ALL_COMPLETED, FIRST_EXCEPTION, ThreadPoolExecutor, wait
from typing import TYPE_CHECKING, overload

from ._errors import AbcError
from ._runner import AigT, check_gia_supported, check_supported, join_commands, resolve_binary, run_script

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from concurrent.futures import Future
    from typing import Literal

__all__ = ["run_many"]


def _default_jobs() -> int:
    """Reports how many ABC processes to keep running at once by default.

    Mirrors what :func:`os.process_cpu_count` does internally, so the interpreters
    that predate it get the same answer rather than an approximation.

    Returns:
        The number of CPUs available to this process, at least one.
    """
    if sys.version_info >= (3, 13):
        return os.process_cpu_count() or 1
    # Only Linux has it, and it is the one that honours CPU affinity -- a batch
    # pinned with `taskset` must not spawn a process per core of the whole machine.
    if hasattr(os, "sched_getaffinity"):
        return len(os.sched_getaffinity(0))
    return os.cpu_count() or 1


def _attribute(exc: BaseException, index: int) -> None:
    """Records which input a failure belongs to on the exception itself.

    Args:
        exc: The failure raised for one network.
        index: Position of that network in the batch.
    """
    # `add_note` is 3.11+, and the package still supports 3.10. The traceback
    # machinery renders notes on its own, which an attribute would not.
    if sys.version_info >= (3, 11):
        exc.add_note(f"raised by run_many() for the network at index {index}")


@overload
def run_many(
    networks: Iterable[AigT],
    commands: str | Sequence[str],
    *,
    jobs: int | None = ...,
    timeout: float | None = ...,
    use_init_file: bool = ...,
    gia: bool = ...,
    binary: str | os.PathLike[str] | None = ...,
    return_exceptions: Literal[False] = False,
) -> list[AigT]: ...


@overload
def run_many(
    networks: Iterable[AigT],
    commands: str | Sequence[str],
    *,
    jobs: int | None = ...,
    timeout: float | None = ...,
    use_init_file: bool = ...,
    gia: bool = ...,
    binary: str | os.PathLike[str] | None = ...,
    return_exceptions: Literal[True],
) -> list[AigT | AbcError]: ...


# For a caller whose `return_exceptions` is decided at runtime. mypy and pyright
# expand a `bool` into its two literals and match the overloads above; `ty` does not.
@overload
def run_many(
    networks: Iterable[AigT],
    commands: str | Sequence[str],
    *,
    jobs: int | None = ...,
    timeout: float | None = ...,
    use_init_file: bool = ...,
    gia: bool = ...,
    binary: str | os.PathLike[str] | None = ...,
    return_exceptions: bool,
) -> list[AigT] | list[AigT | AbcError]: ...


def run_many(
    networks: Iterable[AigT],
    commands: str | Sequence[str],
    *,
    jobs: int | None = None,
    timeout: float | None = None,
    use_init_file: bool = False,
    gia: bool = False,
    binary: str | os.PathLike[str] | None = None,
    return_exceptions: bool = False,
) -> list[AigT] | list[AigT | AbcError]:
    """Runs one ABC script over many networks, in parallel.

    The same script is applied to every network, each in its own ABC process. The
    bridge already isolates a call completely -- its own temporary directory, its
    own working directory, its own ``abc.history`` -- so the runs simply overlap.
    A cross product of scripts and networks is one call per script::

        for name, script in recipes.items():
            rows[name] = abc.run_many(designs, script)

    Results come back in input order, never completion order, so ``zip(networks,
    results)`` is always valid. Every result is held at once regardless of ``jobs``,
    which is the memory a whole corpus costs.

    Expect a speedup below the number of cores. A batch is as slow as its slowest
    network, and the AIGER transfer at each end of a run holds the GIL, so only the
    ABC processes themselves overlap.

    Args:
        networks: The networks to optimize. Consumed in full before any work starts.
        commands: A single ``;``-separated ABC command string, or a sequence of
            individual commands. The same script runs on every network. The
            canonical scripts are reachable through
            :func:`~aigverse.abc.expand_script`.
        jobs: How many ABC processes to keep running at once. ``None`` (default)
            uses the number of CPUs available to this process, capped at the number
            of networks; ``1`` runs inline without a thread pool. On large designs
            memory rather than CPU is what limits this, since each worker holds a
            whole ABC in flight. A CPU *quota* -- ``docker --cpus=2`` -- is not
            visible here, so set ``jobs`` explicitly under one.
        timeout: Seconds to wait for ABC to terminate, **per network** rather than
            for the batch as a whole, or ``None`` for no limit.
        use_init_file: If ``False`` (default), ABC is invoked with ``-s`` so that
            no ``abc.rc`` is read and results do not depend on the local install.
        gia: If ``True``, transfer each network through ``&read``/``&write`` so it
            lands in ABC9's GIA store, as :func:`~aigverse.abc.run_script` does.
        binary: Overrides the resolved ABC executable for this call only. It is
            resolved once for the whole batch.
        return_exceptions: If ``False`` (default), the first failure aborts the
            batch and is raised, as :func:`~aigverse.abc.run_script` would. If
            ``True``, each failing network yields its :exc:`AbcError` in place of a
            result, so one bad design does not lose a whole sweep. Only an
            ``AbcError`` is captured: a ``TypeError`` from an unsupported network
            type, a ``ValueError`` from an invalid script, and anything else that
            goes wrong are raised either way, because those are faults in the call
            rather than per-item ABC failures.

    Returns:
        The optimized networks, in input order, each of the same type as its input
        -- with :exc:`AbcError` instances in place of the failures when
        ``return_exceptions`` is set.

    Raises:
        TypeError: If any element of ``networks`` is not an ``Aig``.
        ValueError: If ``jobs`` is below 1, if no command was given, or if ``gia``
            is set and a network has a register whose reset value is undefined.
        AbcNotFoundError: If no ABC executable could be located. Resolution
            happens once before any network is run, so this is raised whatever
            ``return_exceptions`` says.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds for
            some network and ``return_exceptions`` is not set.
        AbcExecutionError: If ABC reported an error for some network and
            ``return_exceptions`` is not set.

    Note:
        Which failure is reported when several networks fail is unspecified; use
        ``return_exceptions=True`` to see all of them. There is no ``verbose``:
        nothing inside an ABC transcript says which network produced it, so a
        failure's ``output`` -- reachable through ``return_exceptions`` -- is what
        carries that.

    Note:
        Interrupting a batch drops the networks that have not started yet. Ctrl-C in a
        terminal reaches the running ABC processes too, because they share the
        foreground process group, but an interrupt delivered to the interpreter alone
        does not -- ``run_commands`` keeps no handle on what it spawned, so ``timeout``
        is what bounds those.
    """
    items = list(networks)

    # Everything the caller got wrong is reported before a single process starts,
    # so a typo in the script is not discovered one design into a long sweep.
    if jobs is not None and jobs < 1:
        msg = f"jobs must be at least 1, got {jobs}"
        raise ValueError(msg)
    for ntk in items:
        check_supported(ntk)
        if gia:
            check_gia_supported(ntk)
    command = join_commands(commands)

    # Before resolving the binary, so an empty batch is a no-op on a machine
    # without ABC rather than an AbcNotFoundError.
    if not items:
        return []

    executable = resolve_binary(binary)

    def optimize(ntk: AigT) -> AigT:
        """Runs the batch's script on one network.

        Args:
            ntk: The network to optimize.

        Returns:
            The optimized network.
        """
        return run_script(
            ntk,
            command,
            timeout=timeout,
            use_init_file=use_init_file,
            gia=gia,
            binary=executable,
        )

    workers = min(jobs if jobs is not None else _default_jobs(), len(items))
    if workers == 1:
        return _run_serially(items, optimize, return_exceptions=return_exceptions)

    # `max_workers=None` would be min(32, cpu_count + 4); that +4 is tuned for
    # I/O-bound work, while every worker here occupies a core with an ABC process.
    pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="aigverse-abc")
    try:
        futures = [pool.submit(optimize, ntk) for ntk in items]
        wait(futures, return_when=ALL_COMPLETED if return_exceptions else FIRST_EXCEPTION)
    finally:
        # Only drops what has not started. `run_commands` keeps no handle on the
        # process it spawned, so an ABC already running is waited out, not killed.
        pool.shutdown(cancel_futures=True)

    if return_exceptions:
        return _collect(futures)
    return _collect_or_raise(futures)


def _run_serially(
    items: list[AigT],
    optimize: Callable[[AigT], AigT],
    *,
    return_exceptions: bool,
) -> list[AigT] | list[AigT | AbcError]:
    """Runs a batch inline, without a thread pool.

    Keeps ``jobs=1`` a genuine drop-in for a serial loop: no worker frame in the
    traceback, and an interrupt behaves exactly as it does for a single call.

    Args:
        items: The networks to optimize.
        optimize: Runs the batch's script on one network.
        return_exceptions: Whether a failure is returned in place rather than raised.

    Returns:
        The optimized networks, in input order.

    Raises:
        AbcError: If ABC failed on some network and ``return_exceptions`` is not set.
    """
    return [_attempt(optimize, ntk, index, return_exceptions=return_exceptions) for index, ntk in enumerate(items)]


def _attempt(
    optimize: Callable[[AigT], AigT],
    ntk: AigT,
    index: int,
    *,
    return_exceptions: bool,
) -> AigT | AbcError:
    """Runs the batch's script on one network, inline.

    Args:
        optimize: Runs the batch's script on one network.
        ntk: The network to optimize.
        index: Position of that network in the batch.
        return_exceptions: Whether a failure is returned rather than raised.

    Returns:
        The optimized network, or the :exc:`AbcError` it failed with when
        ``return_exceptions`` is set.

    Raises:
        AbcError: If ABC failed and ``return_exceptions`` is not set.
    """
    try:
        return optimize(ntk)
    except AbcError as exc:
        if not return_exceptions:
            _attribute(exc, index)
            raise
        return exc


def _collect(futures: list[Future[AigT]]) -> list[AigT | AbcError]:
    """Gathers a completed batch, keeping each ABC failure in place.

    Args:
        futures: The batch's futures, in input order.

    Returns:
        The optimized networks, with an :exc:`AbcError` in place of each failure.

    Raises:
        BaseException: Whatever a worker raised that was not an ``AbcError``, since
            a disk filling up is not a per-network ABC failure.
    """
    results: list[AigT | AbcError] = []
    for future in futures:
        exc = future.exception()
        if exc is None:
            results.append(future.result())
        elif isinstance(exc, AbcError):
            results.append(exc)
        else:
            raise exc
    return results


def _collect_or_raise(futures: list[Future[AigT]]) -> list[AigT]:
    """Gathers a completed batch, raising the lowest-indexed failure it holds.

    Args:
        futures: The batch's futures, in input order.

    Returns:
        The optimized networks, in input order.

    Raises:
        BaseException: Whatever the lowest-indexed failed network raised.
    """
    for index, future in enumerate(futures):
        # Cancelled means the batch was aborted before this network started.
        if future.cancelled():
            continue
        exc = future.exception()
        if exc is not None:
            _attribute(exc, index)
            raise exc
    return [future.result() for future in futures]
