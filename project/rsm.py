from pyformlang.cfg import Variable
from pyformlang.finite_automaton import EpsilonNFA
from typing import Dict

from project.ecfg import Ecfg


class Rsm:
    def __init__(
        self, boxes: Dict[Variable, EpsilonNFA], start_symbol: Variable = Variable("S")
    ):
        self.boxes = boxes
        self.start_symbol = start_symbol

    @staticmethod
    def from_ecfg(ecfg: "Ecfg") -> "Rsm":
        boxes = {}
        for head, fa in ecfg.productions.items():
            boxes[head] = fa.to_epsilon_nfa()
        return Rsm(boxes=boxes, start_symbol=ecfg.start_symbol)

    def minimize(self) -> "Rsm":
        minimized_boxes = {}
        for n, fa in self.boxes.items():
            minimized_boxes[n] = fa.minimize()

        return Rsm(boxes=minimized_boxes, start_symbol=self.start_symbol)
