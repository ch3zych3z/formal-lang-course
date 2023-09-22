from pyformlang.regular_expression import Regex
from pyformlang.finite_automaton import (
    DeterministicFiniteAutomaton,
    NondeterministicFiniteAutomaton,
)
from networkx import MultiDiGraph
from typing import Set, Any, Union


def dfa_from_regex(regexp: str) -> DeterministicFiniteAutomaton:
    regex = Regex(regexp)
    dfa = regex.to_epsilon_nfa().minimize()
    return dfa


def _set_nodes_flag(
    graph: MultiDiGraph, flag: str, nodes: Union[Set[Any], None]
) -> None:
    nodes = graph.nodes if nodes is None else nodes
    graph.nodes(data=flag, default=False)
    for node in nodes:
        graph.nodes[node][flag] = True


def nfa_from_graph(
    graph: MultiDiGraph, start_nodes: Set[Any] = None, final_nodes: Set[Any] = None
) -> NondeterministicFiniteAutomaton:
    _set_nodes_flag(graph, "is_start", start_nodes)
    _set_nodes_flag(graph, "is_final", final_nodes)

    nfa = NondeterministicFiniteAutomaton.from_networkx(graph)
    return nfa
