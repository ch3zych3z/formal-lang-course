from pyformlang.cfg import CFG, Variable
from pyformlang.regular_expression import Regex
from typing import AbstractSet, Dict


class Ecfg:
    def __init__(
        self,
        variables: AbstractSet[Variable],
        productions: Dict[Variable, Regex],
        start_symbol: Variable = Variable("S"),
    ):
        self.start_symbol = start_symbol
        self.variables = variables
        self.productions = productions

    @staticmethod
    def from_cfg(cfg: CFG) -> "Ecfg":
        productions = {}
        for production in cfg.productions:
            regex_str = (
                " ".join(variable.value for variable in production.body)
                if len(production.body) > 0
                else "$"
            )
            regex = Regex(regex_str)

            head = production.head
            productions[head] = (
                productions[head].union(regex) if head in productions else regex
            )
        return Ecfg(
            variables=cfg.variables,
            productions=productions,
            start_symbol=cfg.start_symbol,
        )

    @staticmethod
    def from_text(text: str, start_symbol: Variable = Variable("S")) -> "Ecfg":
        variables = set()
        productions = {}

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            head_str, body_str = line.split(" -> ")
            head = Variable(head_str)
            variables.add(head)
            productions[head] = Regex(body_str)

        return Ecfg(
            variables=variables, productions=productions, start_symbol=start_symbol
        )

    @staticmethod
    def from_file(path: str) -> "Ecfg":
        with open(path, "r") as f:
            return Ecfg.from_text(f.read())
