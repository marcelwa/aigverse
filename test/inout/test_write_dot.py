from __future__ import annotations

import tempfile
from pathlib import Path

from aigverse.io import write_dot
from aigverse.networks import Aig

# Get the temporary directory as a Path object
temp_dir = Path(tempfile.gettempdir())


def test_write_dot_creates_file() -> None:
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    f = aig.create_and(x1, x2)
    aig.create_po(f)

    dot_path = temp_dir / "aig.dot"
    if dot_path.exists():
        dot_path.unlink()

    write_dot(aig, str(dot_path))
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
