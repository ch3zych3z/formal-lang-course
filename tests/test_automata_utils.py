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


def test_boolean_decompose_and_compose_should_be_id():
    fa = dfa_from_regex("(a.b)*.b|(b.a)*")

    decomposed_fa = BooleanDecomposition.from_fa(fa).compose()

    assert fa.is_equivalent_to(decomposed_fa)


def test_intersection_of_itself_should_be_id():
    fa = dfa_from_regex("(a.b)*.b|(b.a)*")

    intersection = intersect(fa, fa)

    assert fa.is_equivalent_to(intersection)


def test_intersection_should_be_subset_of_operands():
    fa1 = dfa_from_regex("(a.b)*.b.(b.a)*")
    fa2 = dfa_from_regex("a.b*.a")

    intersection = intersect(fa1, fa2)

    assert intersection.is_equivalent_to(intersect(intersection, fa1))
    assert intersection.is_equivalent_to(intersect(intersection, fa2))


def test_intersection_commutativity():
    fa1 = dfa_from_regex("(a.b)*.b.(b.a)*")
    fa2 = dfa_from_regex("a.b*.a")

    intersection1 = intersect(fa1, fa2)
    intersection2 = intersect(fa2, fa1)

    assert intersection1.is_equivalent_to(intersection2)


def test_intersection():
    fa1 = dfa_from_regex("(a.b)*.b.(b.a)*")
    fa2 = dfa_from_regex("a.b*.a")

    intersection = intersect(fa1, fa2)

    expected = fa1.get_intersection(fa2)
    assert expected.is_equivalent_to(intersection)


def test_transitive_closure():
    fa = NondeterministicFiniteAutomaton()
    fa.add_transitions([(0, "a", 1), (1, "a", 2), (2, "a", 0), (3, "a", 2)])

    tc = transitive_closure(fa)

    assert tc[0, 1]
    assert tc[0, 2]
    assert tc[1, 0]
    assert tc[1, 2]
    assert tc[2, 0]
    assert tc[2, 1]
    assert tc[3, 0]
    assert tc[3, 1]
    assert tc[3, 2]
    assert not tc[0, 3]
    assert not tc[1, 3]
    assert not tc[2, 3]
