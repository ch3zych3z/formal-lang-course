from networkx import MultiDiGraph

import project.automata_utils as fau


def intersection_rpq(
    regex: str,
    graph: MultiDiGraph,
    start_states: set = None,
    final_states: set = None
):
    fa1 = fau.nfa_from_graph(graph, start_states, final_states)
    fa2 = fau.dfa_from_regex(regex)

    intersection = fau.intersect(fa1, fa2)
    assert not isinstance(list(intersection.states)[0].value, str)
    transitive_closure = fau.transitive_closure(intersection)
    states = list(intersection.states)

    result = set()
    for row, col in zip(*transitive_closure.nonzero()):
        start_state = states[row]
        final_state = states[col]

        if start_state in intersection.start_states and final_state in intersection.final_states:
            start = start_state.value[0]
            final = final_state.value[0]
            result.add((start, final))

    return result
