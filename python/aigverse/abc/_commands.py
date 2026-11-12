"""Wrappers for the individual ABC optimization commands.

The canonical scripts in :mod:`._wrappers` are sequences of these four commands.
Exposing them individually makes it possible to compose a schedule from Python --
for instance in a reinforcement-learning loop over synthesis actions -- without
assembling ABC command strings by hand.

Every wrapper here is callable on a network, and its ``cmd()`` builds the same
command without running it, so a parameterized command can be handed to
:func:`~aigverse.abc.run_script` or :func:`~aigverse.abc.run_many` like any other.

Every one of these is an ABC builtin, so they work regardless of whether an
``abc.rc`` can be found.

A note on levels: ABC's ``-l`` switch *toggles* a default of "preserve the number
of levels", so passing it turns level preservation off. These wrappers expose the
resulting behaviour directly as ``preserve_levels`` rather than the switch, so
that ``preserve_levels=False`` reads as what it does.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, overload

from ._options import check_option
from ._runner import AigT, Command, CommandWrapper, run_aig_script
from ._runner import run_script as _run_script

if TYPE_CHECKING:
    import os

    from ..networks import Aig, Klut, NamedAig, NamedKlut

__all__ = [
    "Balance",
    "If",
    "Orchestrate",
    "Refactor",
    "Resub",
    "Rewrite",
    "balance",
    "if_",
    "orchestrate",
    "refactor",
    "resub",
    "rewrite",
]


class If(CommandWrapper):
    """Maps a combinational AIG or k-LUT network using ABC's ``if`` command.

    ABC strashes and balances k-LUT input before mapping; AIG input skips that
    preprocessing.
    """

    @staticmethod
    def cmd(
        *,
        cut_size: int = 6,
        cut_limit: int = 8,
        area_oriented_mapping: bool = False,
        area_flow_rounds: int | None = None,
        ela_rounds: int | None = None,
        delay_relaxation: int | None = None,
    ) -> Command:
        """Builds ABC's priority-cut LUT mapping command.

        Args:
            cut_size: Maximum LUT inputs (2 through 32).
            cut_limit: Maximum priority cuts per node (1 through 4095).
            area_oriented_mapping: Optimize area instead of delay.
            area_flow_rounds: Area-flow recovery iterations (``-F``), at least
                zero; ``None`` keeps ABC's default of 1.
            ela_rounds: Exact-area recovery iterations (``-A``), at least zero;
                ``None`` keeps ABC's default of 2.
            delay_relaxation: Delay relaxation percentage (``-R``), at least
                zero; ``None`` keeps ABC's default of 0.

        Returns:
            The command for a script requesting ``output_type='klut'``.

        Raises:
            ValueError: If an option is outside ABC's accepted integer range.
        """
        command = "if"
        for switch, value, name in (
            ("K", cut_size, "cut_size"),
            ("C", cut_limit, "cut_limit"),
            ("F", area_flow_rounds, "area_flow_rounds"),
            ("A", ela_rounds, "ela_rounds"),
            ("R", delay_relaxation, "delay_relaxation"),
        ):
            if value is None and switch not in {"K", "C"}:
                continue
            # ABC parses these switches with atoi into a signed 32-bit int.
            if not isinstance(value, int) or isinstance(value, bool) or value > 2**31 - 1:
                msg = f"{name} must be an integer no larger than {2**31 - 1}, got {value}"
                raise ValueError(msg)
            check_option("if", switch, value, name=name)
            command += f" -{switch} {value}"
        if area_oriented_mapping:
            command += " -a"
        return Command(command)

    @overload
    def __call__(
        self,
        ntk: NamedAig | NamedKlut,
        *,
        cut_size: int = ...,
        cut_limit: int = ...,
        area_oriented_mapping: bool = ...,
        area_flow_rounds: int | None = ...,
        ela_rounds: int | None = ...,
        delay_relaxation: int | None = ...,
        timeout: float | None = ...,
        verbose: bool = ...,
        binary: str | os.PathLike[str] | None = ...,
    ) -> NamedKlut: ...

    @overload
    def __call__(
        self,
        ntk: Aig | Klut,
        *,
        cut_size: int = ...,
        cut_limit: int = ...,
        area_oriented_mapping: bool = ...,
        area_flow_rounds: int | None = ...,
        ela_rounds: int | None = ...,
        delay_relaxation: int | None = ...,
        timeout: float | None = ...,
        verbose: bool = ...,
        binary: str | os.PathLike[str] | None = ...,
    ) -> Klut: ...

    def __call__(
        self,
        ntk: Aig | Klut,
        *,
        cut_size: int = 6,
        cut_limit: int = 8,
        area_oriented_mapping: bool = False,
        area_flow_rounds: int | None = None,
        ela_rounds: int | None = None,
        delay_relaxation: int | None = None,
        timeout: float | None = None,
        verbose: bool = False,
        binary: str | os.PathLike[str] | None = None,
    ) -> Klut:
        """Maps a network into k-LUTs without changing its source.

        Args:
            ntk: A combinational AIG or k-LUT network.
            cut_size: Maximum LUT inputs (2 through 32).
            cut_limit: Maximum priority cuts per node (1 through 4095).
            area_oriented_mapping: Optimize area instead of delay.
            area_flow_rounds: Area-flow recovery iterations, or ``None`` for 1.
            ela_rounds: Exact-area recovery iterations, or ``None`` for 2.
            delay_relaxation: Delay relaxation percentage, or ``None`` for 0.
            timeout: Seconds to wait for ABC, or ``None`` for no limit.
            verbose: Whether to print ABC's captured output.
            binary: Optional executable override.

        Returns:
            A ``NamedKlut`` for a named input, otherwise a ``Klut``.

        Raises:
            ValueError: If an option is invalid or the input is sequential.
        """
        command = self.cmd(
            cut_size=cut_size,
            cut_limit=cut_limit,
            area_oriented_mapping=area_oriented_mapping,
            area_flow_rounds=area_flow_rounds,
            ela_rounds=ela_rounds,
            delay_relaxation=delay_relaxation,
        )
        return _run_script(ntk, command, output_type="klut", timeout=timeout, verbose=verbose, binary=binary)


if_: Final[If] = If()
"""Maps to k-LUTs with ABC's ``if`` command, or builds it; see :class:`If`."""


class Balance(CommandWrapper):
    """Runs ABC's ``balance`` command on a network, or builds it as a command."""

    @staticmethod
    def cmd(
        *,
        minimize_levels: bool = True,
        exor: bool = False,
        duplicate: bool = False,
        duplicate_critical: bool = False,
    ) -> Command:
        """Builds ABC's ``balance`` command without running it.

        Args:
            minimize_levels: If ``True`` (ABC's default), balance for minimal depth.
            exor: If ``True``, balance multi-input EXOR structures as well.
            duplicate: If ``True``, allow logic to be duplicated.
            duplicate_critical: If ``True``, duplicate logic on the critical paths
                only, which buys depth for less area than ``duplicate`` does.

        Returns:
            The command, ready for :func:`~aigverse.abc.run_script` or
            :func:`~aigverse.abc.run_many`.
        """
        command = "balance"
        if not minimize_levels:
            command += " -l"
        if duplicate:
            command += " -d"
        if duplicate_critical:
            command += " -s"
        if exor:
            command += " -x"
        return Command(command)

    def __call__(
        self,
        ntk: AigT,
        *,
        minimize_levels: bool = True,
        exor: bool = False,
        duplicate: bool = False,
        duplicate_critical: bool = False,
        timeout: float | None = None,
        verbose: bool = False,
        binary: str | os.PathLike[str] | None = None,
    ) -> AigT:
        """Runs ABC's ``balance`` command on a network.

        Restructures the AND trees of the network to reduce its depth.

        Args:
            ntk: The network to optimize.
            minimize_levels: If ``True`` (ABC's default), balance for minimal depth.
            exor: If ``True``, balance multi-input EXOR structures as well.
            duplicate: If ``True``, allow logic to be duplicated.
            duplicate_critical: If ``True``, duplicate logic on the critical paths
                only, which buys depth for less area than ``duplicate`` does.
            timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
            verbose: If ``True``, print everything ABC wrote.
            binary: Overrides the resolved ABC executable for this call only.

        Returns:
            The optimized network, of the same type as ``ntk``.
        """
        command = self.cmd(
            minimize_levels=minimize_levels,
            exor=exor,
            duplicate=duplicate,
            duplicate_critical=duplicate_critical,
        )
        return run_aig_script(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


balance: Final[Balance] = Balance()
"""Runs ABC's ``balance`` command on a network, or builds it as a command; see :class:`Balance`."""


class Rewrite(CommandWrapper):
    """Runs ABC's ``rewrite`` command on a network, or builds it as a command."""

    @staticmethod
    def cmd(*, preserve_levels: bool = True, zero_cost: bool = False) -> Command:
        """Builds ABC's ``rewrite`` command without running it.

        Args:
            preserve_levels: If ``True`` (ABC's default), never increase the depth.
            zero_cost: If ``True``, also apply replacements that do not reduce the
                size, which perturbs the structure and can unlock later gains.

        Returns:
            The command, ready for :func:`~aigverse.abc.run_script` or
            :func:`~aigverse.abc.run_many`.
        """
        command = "rewrite"
        if not preserve_levels:
            command += " -l"
        if zero_cost:
            command += " -z"
        return Command(command)

    def __call__(
        self,
        ntk: AigT,
        *,
        preserve_levels: bool = True,
        zero_cost: bool = False,
        timeout: float | None = None,
        verbose: bool = False,
        binary: str | os.PathLike[str] | None = None,
    ) -> AigT:
        """Runs ABC's ``rewrite`` command on a network.

        Replaces 4-input subgraphs with smaller pre-computed equivalents.

        Args:
            ntk: The network to optimize.
            preserve_levels: If ``True`` (ABC's default), never increase the depth.
            zero_cost: If ``True``, also apply replacements that do not reduce the
                size, which perturbs the structure and can unlock later gains.
            timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
            verbose: If ``True``, print everything ABC wrote.
            binary: Overrides the resolved ABC executable for this call only.

        Returns:
            The optimized network, of the same type as ``ntk``.
        """
        command = self.cmd(preserve_levels=preserve_levels, zero_cost=zero_cost)
        return run_aig_script(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


rewrite: Final[Rewrite] = Rewrite()
"""Runs ABC's ``rewrite`` command on a network, or builds it as a command; see :class:`Rewrite`."""


class Refactor(CommandWrapper):
    """Runs ABC's ``refactor`` command on a network, or builds it as a command."""

    @staticmethod
    def cmd(
        *,
        max_support: int | None = None,
        min_saved: int | None = None,
        preserve_levels: bool = True,
        zero_cost: bool = False,
    ) -> Command:
        """Builds ABC's ``refactor`` command without running it.

        Args:
            max_support: Maximum support of a collapsed node (ABC's ``-N``, 1 to 15),
                or ``None`` for ABC's default of 10. Larger values are slower. ABC
                documents no range but rejects anything above 15.
            min_saved: Minimum number of nodes a single step must save to be applied
                (ABC's ``-M``, at least 0), or ``None`` for ABC's default of 1.
                Setting it to 0 accepts steps that save nothing.
            preserve_levels: If ``True`` (ABC's default), never increase the depth.
            zero_cost: If ``True``, also apply replacements that do not reduce the
                size, which perturbs the structure and can unlock later gains.

        Returns:
            The command, ready for :func:`~aigverse.abc.run_script` or
            :func:`~aigverse.abc.run_many`.

        Raises:
            ValueError: If ``max_support`` is outside the range ABC accepts.
        """
        command = "refactor"
        if max_support is not None:
            check_option("refactor", "N", max_support, name="max_support")
            command += f" -N {max_support}"
        if min_saved is not None:
            check_option("refactor", "M", min_saved, name="min_saved")
            command += f" -M {min_saved}"
        if not preserve_levels:
            command += " -l"
        if zero_cost:
            command += " -z"
        return Command(command)

    def __call__(
        self,
        ntk: AigT,
        *,
        max_support: int | None = None,
        min_saved: int | None = None,
        preserve_levels: bool = True,
        zero_cost: bool = False,
        timeout: float | None = None,
        verbose: bool = False,
        binary: str | os.PathLike[str] | None = None,
    ) -> AigT:
        """Runs ABC's ``refactor`` command on a network.

        Collapses a cone into a single node and resynthesizes it from its truth
        table, which reaches larger cuts than :obj:`rewrite` does.

        Args:
            ntk: The network to optimize.
            max_support: Maximum support of a collapsed node (ABC's ``-N``, 1 to 15),
                or ``None`` for ABC's default of 10. Larger values are slower. ABC
                documents no range but rejects anything above 15.
            min_saved: Minimum number of nodes a single step must save to be applied
                (ABC's ``-M``, at least 0), or ``None`` for ABC's default of 1.
                Setting it to 0 accepts steps that save nothing.
            preserve_levels: If ``True`` (ABC's default), never increase the depth.
            zero_cost: If ``True``, also apply replacements that do not reduce the
                size, which perturbs the structure and can unlock later gains.
            timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
            verbose: If ``True``, print everything ABC wrote.
            binary: Overrides the resolved ABC executable for this call only.

        Returns:
            The optimized network, of the same type as ``ntk``.

        Raises:
            ValueError: If ``max_support`` is outside the range ABC accepts.
        """
        command = self.cmd(
            max_support=max_support,
            min_saved=min_saved,
            preserve_levels=preserve_levels,
            zero_cost=zero_cost,
        )
        return run_aig_script(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


refactor: Final[Refactor] = Refactor()
"""Runs ABC's ``refactor`` command on a network, or builds it as a command; see :class:`Refactor`."""


class Resub(CommandWrapper):
    """Runs ABC's ``resub`` command on a network, or builds it as a command."""

    @staticmethod
    def cmd(
        *,
        max_cut_size: int | None = None,
        max_inserts: int | None = None,
        min_saved: int | None = None,
        odc_levels: int | None = None,
        preserve_levels: bool = True,
        zero_cost: bool = False,
    ) -> Command:
        """Builds ABC's ``resub`` command without running it.

        Args:
            max_cut_size: Maximum cut size (ABC's ``-K``, 4 to 16), or ``None`` for
                ABC's default of 8. The canonical scripts sweep this from 6 to 12.
            max_inserts: Maximum number of nodes to add (ABC's ``-N``, 0 to 3), or
                ``None`` for ABC's default of 1.
            min_saved: Minimum number of nodes a single step must save to be applied
                (ABC's ``-M``, at least 0), or ``None`` for ABC's default of 1.
            odc_levels: Fanout levels used for observability-don't-care computation
                (ABC's ``-F``, at least 0), or ``None`` for ABC's default of 0, which
                disables it. Don't-cares find substitutions that are only valid in
                context, at the cost of a more expensive analysis.
            preserve_levels: If ``True`` (ABC's default), never increase the depth.
            zero_cost: If ``True``, also apply replacements that do not reduce the
                size, which perturbs the structure and can unlock later gains.

        Returns:
            The command, ready for :func:`~aigverse.abc.run_script` or
            :func:`~aigverse.abc.run_many`.

        Raises:
            ValueError: If ``max_cut_size`` or ``max_inserts`` is outside the range
                ABC accepts.
        """
        command = "resub"
        if max_cut_size is not None:
            check_option("resub", "K", max_cut_size, name="max_cut_size")
            command += f" -K {max_cut_size}"
        if max_inserts is not None:
            check_option("resub", "N", max_inserts, name="max_inserts")
            command += f" -N {max_inserts}"
        if min_saved is not None:
            check_option("resub", "M", min_saved, name="min_saved")
            command += f" -M {min_saved}"
        if odc_levels is not None:
            check_option("resub", "F", odc_levels, name="odc_levels")
            command += f" -F {odc_levels}"
        if not preserve_levels:
            command += " -l"
        if zero_cost:
            command += " -z"
        return Command(command)

    def __call__(
        self,
        ntk: AigT,
        *,
        max_cut_size: int | None = None,
        max_inserts: int | None = None,
        min_saved: int | None = None,
        odc_levels: int | None = None,
        preserve_levels: bool = True,
        zero_cost: bool = False,
        timeout: float | None = None,
        verbose: bool = False,
        binary: str | os.PathLike[str] | None = None,
    ) -> AigT:
        """Runs ABC's ``resub`` command on a network.

        Re-expresses a node in terms of other nodes already present, which removes
        logic that rewriting and refactoring cannot reach because it is not local.

        Args:
            ntk: The network to optimize.
            max_cut_size: Maximum cut size (ABC's ``-K``, 4 to 16), or ``None`` for
                ABC's default of 8. The canonical scripts sweep this from 6 to 12.
            max_inserts: Maximum number of nodes to add (ABC's ``-N``, 0 to 3), or
                ``None`` for ABC's default of 1.
            min_saved: Minimum number of nodes a single step must save to be applied
                (ABC's ``-M``, at least 0), or ``None`` for ABC's default of 1.
            odc_levels: Fanout levels used for observability-don't-care computation
                (ABC's ``-F``, at least 0), or ``None`` for ABC's default of 0, which
                disables it. Don't-cares find substitutions that are only valid in
                context, at the cost of a more expensive analysis.
            preserve_levels: If ``True`` (ABC's default), never increase the depth.
            zero_cost: If ``True``, also apply replacements that do not reduce the
                size, which perturbs the structure and can unlock later gains.
            timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
            verbose: If ``True``, print everything ABC wrote.
            binary: Overrides the resolved ABC executable for this call only.

        Returns:
            The optimized network, of the same type as ``ntk``.

        Raises:
            ValueError: If ``max_cut_size`` or ``max_inserts`` is outside the range
                ABC accepts.
        """
        command = self.cmd(
            max_cut_size=max_cut_size,
            max_inserts=max_inserts,
            min_saved=min_saved,
            odc_levels=odc_levels,
            preserve_levels=preserve_levels,
            zero_cost=zero_cost,
        )
        return run_aig_script(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


resub: Final[Resub] = Resub()
"""Runs ABC's ``resub`` command on a network, or builds it as a command; see :class:`Resub`."""


class Orchestrate(CommandWrapper):
    """Runs ABC's ``orchestrate`` command on a network, or builds it as a command."""

    @staticmethod
    def cmd(
        *,
        max_cut_size: int | None = None,
        max_inserts: int | None = None,
        odc_levels: int | None = None,
        preserve_levels: bool = True,
        zero_cost_rewrite: bool = True,
        zero_cost_refactor: bool = True,
    ) -> Command:
        """Builds ABC's ``orchestrate`` command without running it.

        Args:
            max_cut_size: Resubstitution cut size (ABC's ``-K``, 4 to 16), or ``None``
                for ABC's default of 8.
            max_inserts: Nodes resubstitution may add (ABC's ``-N``, 0 to 3), or
                ``None`` for ABC's default of 1.
            odc_levels: Fanout levels used for don't-care computation (ABC's ``-F``),
                or ``None`` for ABC's default of 0.
            preserve_levels: If ``True`` (ABC's default), never increase the depth.
            zero_cost_rewrite: If ``True`` (ABC's default here), let the rewriting
                part apply replacements that do not reduce the size.
            zero_cost_refactor: If ``True`` (ABC's default here), the same for the
                refactoring part.

        Returns:
            The command, ready for :func:`~aigverse.abc.run_script` or
            :func:`~aigverse.abc.run_many`.

        Raises:
            ValueError: If an option is outside the range ABC accepts.
        """
        command = "orchestrate"
        if max_cut_size is not None:
            check_option("orchestrate", "K", max_cut_size, name="max_cut_size")
            command += f" -K {max_cut_size}"
        if max_inserts is not None:
            check_option("orchestrate", "N", max_inserts, name="max_inserts")
            command += f" -N {max_inserts}"
        if odc_levels is not None:
            check_option("orchestrate", "F", odc_levels, name="odc_levels")
            command += f" -F {odc_levels}"
        # every one of these switches toggles a default of "on"
        if not preserve_levels:
            command += " -l"
        if not zero_cost_rewrite:
            command += " -z"
        if not zero_cost_refactor:
            command += " -Z"
        return Command(command)

    def __call__(
        self,
        ntk: AigT,
        *,
        max_cut_size: int | None = None,
        max_inserts: int | None = None,
        odc_levels: int | None = None,
        preserve_levels: bool = True,
        zero_cost_rewrite: bool = True,
        zero_cost_refactor: bool = True,
        timeout: float | None = None,
        verbose: bool = False,
        binary: str | os.PathLike[str] | None = None,
    ) -> AigT:
        """Runs ABC's ``orchestrate`` command on a network.

        Interleaves rewriting, refactoring and resubstitution rather than running
        them one after another, choosing per node which of the three to apply. It is
        a single command doing the job of a whole schedule.

        Note that ABC enables zero-cost replacements here by default, unlike in the
        standalone :obj:`rewrite` and :obj:`refactor` commands.

        Args:
            ntk: The network to optimize.
            max_cut_size: Resubstitution cut size (ABC's ``-K``, 4 to 16), or ``None``
                for ABC's default of 8.
            max_inserts: Nodes resubstitution may add (ABC's ``-N``, 0 to 3), or
                ``None`` for ABC's default of 1.
            odc_levels: Fanout levels used for don't-care computation (ABC's ``-F``),
                or ``None`` for ABC's default of 0.
            preserve_levels: If ``True`` (ABC's default), never increase the depth.
            zero_cost_rewrite: If ``True`` (ABC's default here), let the rewriting
                part apply replacements that do not reduce the size.
            zero_cost_refactor: If ``True`` (ABC's default here), the same for the
                refactoring part.
            timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
            verbose: If ``True``, print everything ABC wrote.
            binary: Overrides the resolved ABC executable for this call only.

        Returns:
            The optimized network, of the same type as ``ntk``.

        Raises:
            ValueError: If an option is outside the range ABC accepts.
        """
        command = self.cmd(
            max_cut_size=max_cut_size,
            max_inserts=max_inserts,
            odc_levels=odc_levels,
            preserve_levels=preserve_levels,
            zero_cost_rewrite=zero_cost_rewrite,
            zero_cost_refactor=zero_cost_refactor,
        )
        return run_aig_script(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


orchestrate: Final[Orchestrate] = Orchestrate()
"""Runs ABC's ``orchestrate`` command on a network, or builds it as a command; see :class:`Orchestrate`."""
