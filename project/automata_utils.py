from pyformlang.regular_expression import Regex
from pyformlang.finite_automaton import (
    DeterministicFiniteAutomaton,
    NondeterministicFiniteAutomaton,
    FiniteAutomaton,
    EpsilonNFA,
    State,
)
from networkx import MultiDiGraph
from typing import Set, Any, Union, KeysView, TypeVar, Dict, List
from scipy import sparse


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


class BooleanDecomposition:
    T = TypeVar("T")

    def __init__(
        self,
        states_indices: Dict[T, int],
        label_matrices,
        states: List[T],
        start_states: Set[T],
        final_states: Set[T],
    ):
        self.__states_indices = states_indices
        self.__label_matrices = label_matrices
        self.__start_states = start_states
        self.__final_states = final_states
        self.__states = states

    @staticmethod
    def from_fa(fa: FiniteAutomaton):
        label_matrices = {}
        states_count = len(fa.states)
        states_indices = {state: ind for (ind, state) in enumerate(fa.states)}

        for source, transitions_from_source in fa.to_dict().items():
            for label, destinations in transitions_from_source.items():
                if not isinstance(destinations, set):
                    destinations = {destinations}

                for destination in destinations:
                    if label not in label_matrices:
                        label_matrices[label] = sparse.dok_matrix(
                            (states_count, states_count), dtype=bool
                        )
                    source_ind = states_indices[source]
                    destination_ind = states_indices[destination]
                    label_matrices[label][source_ind, destination_ind] = True

        return BooleanDecomposition(
            states_indices,
            label_matrices,
            list(fa.states),
            fa.start_states,
            fa.final_states,
        )

    def __getitem__(self, label: Any):
        return self.__label_matrices[label]

    @property
    def labels(self) -> KeysView[Any]:
        return self.__label_matrices.keys()

    def index_of(self, state: Any) -> int:
        return self.__states_indices[state]

    def compose(self) -> FiniteAutomaton:
        fa = EpsilonNFA()

        for label, matrix in self.__label_matrices.items():
            rows, cols = matrix.nonzero()
            for row, col in zip(rows, cols):
                source = self.__states[row]
                dest = self.__states[col]
                fa.add_transition(source, label, dest)

        for state in self.__start_states:
            fa.add_start_state(state)
        for state in self.__final_states:
            fa.add_final_state(state)

        return fa


def intersect(fa1: FiniteAutomaton, fa2: FiniteAutomaton) -> FiniteAutomaton:
    bdecomp1 = BooleanDecomposition.from_fa(fa1)
    bdecomp2 = BooleanDecomposition.from_fa(fa2)

    states_count2 = len(fa2.states)
    labels = bdecomp1.labels & bdecomp2.labels

    intersected_label_matrices = {}
    states_indices = {}
    start_states = set()
    final_states = set()

    for label in labels:
        intersected_label_matrices[label] = sparse.kron(
            bdecomp1[label], bdecomp2[label]
        )

    states = []
    for state1 in fa1.states:
        for state2 in fa2.states:
            state_index = states_count2 * bdecomp1.index_of(state1) + bdecomp2.index_of(
                state2
            )

            state = State((state1.value, state2.value))
            states_indices[state] = state_index
            states.append(state)
            if state1 in fa1.start_states and state2 in fa2.start_states:
                start_states.add(state)
            if state1 in fa1.final_states and state2 in fa2.final_states:
                final_states.add(state)

    return BooleanDecomposition(
        states_indices, intersected_label_matrices, states, start_states, final_states
    ).compose()


def transitive_closure(fa: FiniteAutomaton):
    states_count = len(fa.states)
    if states_count == 0:
        return sparse.dok_matrix((0, 0), dtype=bool)

    states_indices = {state: ind for (ind, state) in enumerate(fa.states)}
    transitive_closure = sparse.dok_matrix((states_count, states_count), dtype=bool)
    for source, transitions_from_source in fa.to_dict().items():
        for destinations in transitions_from_source.values():
            if not isinstance(destinations, set):
                destinations = {destinations}

            for destination in destinations:
                source_ind = states_indices[source]
                destination_ind = states_indices[destination]
                transitive_closure[source_ind, destination_ind] = True

    prev = transitive_closure.nnz
    curr = 0

    while prev != curr:
        transitive_closure += transitive_closure @ transitive_closure
        prev = curr
        curr = transitive_closure.nnz

    return transitive_closure
