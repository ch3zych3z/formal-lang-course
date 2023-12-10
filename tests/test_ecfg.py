import pytest
from pyformlang.cfg import CFG, Variable
from pyformlang.regular_expression import Regex

from project.ecfg import Ecfg


def _is_regexes_equal(regex1: Regex, regex2: Regex) -> bool:
    return regex1.to_epsilon_nfa().is_equivalent_to(regex2.to_epsilon_nfa())


@pytest.mark.parametrize(
    "cfg, expected_productions",
    [
        (
            """
            S -> epsilon
            """,
            {Variable("S"): Regex("$")},
        ),
        (
            """
            S -> a S b S
            S -> epsilon
            """,
            {Variable("S"): Regex("(a S b S) | $")},
        ),
        (
            """
            S -> a S b
            S -> S S
            S -> epsilon
            """,
            {Variable("S"): Regex("(S S) | (a S b) | $")},
        ),
    ],
)
def test_from_cfg(cfg, expected_productions):
    ecfg = Ecfg.from_cfg(CFG.from_text(cfg))
    ecfg_productions = ecfg.productions.items()
    assert len(ecfg_productions) == len(expected_productions)
    for head, production in ecfg_productions:
        assert _is_regexes_equal(production, expected_productions[head])


@pytest.mark.parametrize(
    "text, expected_productions",
    [
        (
            """
            S -> epsilon
            """,
            {Variable("S"): Regex("$")},
        ),
        (
            """
            S -> (a S b S) | epsilon
            """,
            {Variable("S"): Regex("(a S b S) | $")},
        ),
        (
            """
            S -> (a S b) | (S S) | epsilon
            """,
            {Variable("S"): Regex("(S S) | (a S b) | $")},
        ),
    ],
)
def test_from_text(text, expected_productions):
    ecfg = Ecfg.from_text(text)
    ecfg_productions = ecfg.productions.items()
    assert len(ecfg_productions) == len(expected_productions)
    for head, production in ecfg_productions:
        assert _is_regexes_equal(production, expected_productions[head])
