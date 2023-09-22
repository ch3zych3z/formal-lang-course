import cfpq_data

from project.automata_utils import *


def test_dfa_from_regex():
    dfa = dfa_from_regex("(a.b)*")

    minimized = dfa.minimize()
    assert dfa.is_deterministic()
    assert dfa.is_equivalent_to(minimized)


def test_nfa_from_graph_with_no_starting_nodes():
    graph = cfpq_data.labeled_two_cycles_graph(2, 10)
    final_nodes = {0, 3}

    nfa = nfa_from_graph(graph, final_nodes=final_nodes)

    assert nfa.start_states == set(graph)
    assert nfa.final_states == final_nodes


def test_nfa_from_graph_with_no_final_nodes():
    graph = cfpq_data.labeled_two_cycles_graph(2, 10)
    start_nodes = {0, 3}

    nfa = nfa_from_graph(graph, start_nodes=start_nodes)

    assert nfa.final_states == set(graph)
    assert nfa.start_states == start_nodes
