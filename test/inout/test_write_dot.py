from __future__ import annotations

from typing import TYPE_CHECKING

from aigverse.io import write_dot

if TYPE_CHECKING:
    from pathlib import Path

    from aigverse.networks import Aig


def test_write_dot_creates_file(simple_and_aig: Aig, tmp_path: Path) -> None:
    dot_path = tmp_path / "aig.dot"

    write_dot(simple_and_aig, str(dot_path))
    assert dot_path.exists()

    content = dot_path.read_text()

    expected = """
    digraph {
        rankdir=BT;

        0 [label="0",shape=box,style=filled,fillcolor=snow2]
        1 [label="1",shape=triangle,style=filled,fillcolor=snow2]
        2 [label="2",shape=triangle,style=filled,fillcolor=snow2]
        3 [label="3",shape=ellipse,style=filled,fillcolor=white]

        po0 [shape=invtriangle,style=filled,fillcolor=snow2]

        1 -> 3 [style=solid]
        2 -> 3 [style=solid]
        3 -> po0 [style=solid]

        {rank = same; 0; 1; 2; }
        {rank = same; 3; }
        {rank = same; po0; }
    }
    """

    def normalize(s: str) -> str:
        return "".join(s.split())

    assert normalize(content) == normalize(expected)
