from project.cfg_utils import *

import pytest
from pyformlang.cfg import Terminal


path = "tests/resources/cfg/converter"


def test_removed_unused():
    cfg = from_file(f"{path}/1.cfg")
    wcnf = to_wcnf(cfg)

    assert Terminal("C") in cfg.variables
    assert Terminal("C") not in wcnf.variables


def _is_wcnf(cfg: CFG) -> bool:
    for production in cfg.productions:
        body = production.body
        length = len(body)
        if not (
            (length == 2 and body[0] in cfg.variables and body[1] in cfg.variables)
            or (length == 1 and body[0] in cfg.terminals)
            or (not body)
        ):
            return False
    return True


@pytest.mark.parametrize(
    "filename", [pytest.param(f"{path}/{i}.cfg") for i in range(1, 5)]
)
def test_converter(filename):
    wcnf = to_wcnf(from_file(filename))

    assert _is_wcnf(wcnf)
