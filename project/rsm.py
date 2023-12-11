from pyformlang.cfg import Variable
from pyformlang.finite_automaton import EpsilonNFA, State
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
        for head, regex in ecfg.productions.items():
            boxes[head] = regex.to_epsilon_nfa()
        return Rsm(boxes=boxes, start_symbol=ecfg.start_symbol)

    def minimize(self) -> "Rsm":
        minimized_boxes = {}
        for n, fa in self.boxes.items():
            minimized_boxes[n] = fa.minimize()

        return Rsm(boxes=minimized_boxes, start_symbol=self.start_symbol)

    def merge_boxes(self):
        nfa = EpsilonNFA()
        for nonterm, fa in self.boxes.items():
            for start_state in fa.start_states:
                nfa.add_start_state(State((nonterm, start_state)))
            for final_state in fa.final_states:
                nfa.add_final_state(State((nonterm, final_state)))
            nfa.add_transitions(
                (State((nonterm, start)), label, State((nonterm, end)))
                for (start, label, end) in fa
            )
        return nfa
