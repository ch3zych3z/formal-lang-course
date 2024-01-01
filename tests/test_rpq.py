import cfpq_data
from pyformlang.finite_automaton import NondeterministicFiniteAutomaton, State, Symbol

from project.rpq import *


def test_rpq1():
    automaton = NondeterministicFiniteAutomaton()
    automaton.add_transition(State(0), Symbol("a"), State(1))
    automaton.add_transition(State(1), Symbol("b"), State(2))
    automaton.add_transition(State(0), Symbol("a"), State(3))
    automaton.add_transition(State(3), Symbol("c"), State(4))
    graph = automaton.to_networkx()

    assert intersection_rpq("(a|f).(b|d)", graph, {0}, {2, 4}) == {(0, 2)}


def test_rpq2():
    graph = cfpq_data.labeled_two_cycles_graph(3, 3, labels=("a", "b"), common_node=0)
    regex = "(a|b)(aa)*"

    assert intersection_rpq(regex, graph, {0}, {1}) == {(0, 1)}


def test_rpq_reachability():
    automaton = NondeterministicFiniteAutomaton()
    automaton.add_transition(State(0), Symbol("a"), State(1))
    automaton.add_transition(State(1), Symbol("a"), State(2))
    automaton.add_transition(State(2), Symbol("a"), State(0))
    automaton.add_transition(State(4), Symbol("a"), State(5))
    graph = automaton.to_networkx()

    regex = "a*"

    result = intersection_rpq(regex, graph, {0, 1, 2}, {0, 1, 2})

    assert len(result) == 9


def test_bfs_rpq_reachability():
    graph = MultiDiGraph()
    graph.add_edges_from(
        [
            (0, 1, {"label": "a"}),
            (1, 2, {"label": "b"}),
            (2, 3, {"label": "a"}),
            (3, 4, {"label": "b"}),
            (0, 2, {"label": "a"}),
            (2, 5, {"label": "b"}),
            (3, 6, {"label": "a"}),
            (6, 0, {"label": "b"}),
        ]
    )
    regex = "(a|b)*"
    assert bfs_rpq(regex, graph) == {0, 1, 2, 3, 4, 5, 6}


def test_bfs_rpq_separated_start():
    graph = MultiDiGraph()
    graph.add_edges_from(
        [
            (0, 1, {"label": "a"}),
            (0, 2, {"label": "b"}),
            (1, 2, {"label": "b"}),
            (2, 2, {"label": "c"}),
        ]
    )
    regex = "a.b*"
    result = bfs_rpq(regex, graph, {0, 1}, {2}, True)
    assert result == {(0, 2), (1, 2)}


def test_empty_bfs_rpq():
    graph = MultiDiGraph()
    assert bfs_rpq("abacaba", graph) == set()
