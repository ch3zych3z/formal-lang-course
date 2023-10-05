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


def adjacency_matrix(fa: FiniteAutomaton):
    states_count = len(fa.states)
    if states_count == 0:
        return sparse.dok_matrix((0, 0), dtype=bool)

    states_indices = {state: ind for (ind, state) in enumerate(fa.states)}
    adj_matrix = sparse.dok_matrix((states_count, states_count), dtype=bool)
    for source, transitions_from_source in fa.to_dict().items():
        for destinations in transitions_from_source.values():
            if not isinstance(destinations, set):
                destinations = {destinations}

            for destination in destinations:
                source_ind = states_indices[source]
                destination_ind = states_indices[destination]
                adj_matrix[source_ind, destination_ind] = True
    return adj_matrix


def transitive_closure(fa: FiniteAutomaton):
    closure = adjacency_matrix(fa)

    prev = closure.nnz
    curr = 0

    while prev != curr:
        closure += closure @ closure
        prev = curr
        curr = closure.nnz

    return closure


def _create_front(fa: FiniteAutomaton, constraint: FiniteAutomaton):
    n = len(fa.states)
    k = len(constraint.states)

    front = sparse.lil_matrix((k, n + k))

    tail = sparse.lil_array([[state in fa.start_states for state in fa.states]])

    for i in range(k):
        front[i, i] = True
        front[i, k:] = tail

    return front.tocsr()


def _transform_front(front, constraint_states_cnt: int, separated_start):
    new_front = sparse.csr_matrix(front.shape, dtype=bool)
    for row, col in zip(*front.nonzero()):
        if col < constraint_states_cnt:
            row_tail = front[row, constraint_states_cnt:]
            if row_tail.nnz != 0:
                shifted_row = (
                    row // constraint_states_cnt * constraint_states_cnt + col
                    if separated_start
                    else col
                )
                new_front[shifted_row, col] = True
                new_front[shifted_row, constraint_states_cnt:] += row_tail
    return new_front


def constraint_reachability(
    fa: FiniteAutomaton,
    constraint: FiniteAutomaton,
    separated_start: bool = False,
):
    decomp_fa = BooleanDecomposition.from_fa(fa)
    decomp_constraint = BooleanDecomposition.from_fa(constraint)
    constr_states_cnt = len(constraint.states)
    labels = decomp_fa.labels & decomp_constraint.labels

    direct_sum = {}
    for label in labels:
        direct_sum[label] = sparse.block_diag(
            (decomp_constraint[label], decomp_fa[label])
        )

    front = (
        sparse.vstack([_create_front(fa, constraint) for _ in fa.start_states])
        if separated_start
        else _create_front(fa, constraint)
    )

    front_nnz = -1
    while front_nnz != front.nnz:
        front_nnz = front.nnz

        for mtx in direct_sum.values():
            step = front @ mtx
            front += _transform_front(step, constr_states_cnt, separated_start)

    result = set()
    constraint_states = list(constraint.states)
    fa_states = list(fa.states)

    for row, col in zip(*front.nonzero()):
        if (
            not col < constr_states_cnt
            and constraint_states[row % constr_states_cnt] in constraint.final_states
        ):
            state_index = col - constr_states_cnt
            if fa_states[state_index] in fa.final_states:
                if separated_start:
                    result.add((State(row // constr_states_cnt), State(state_index)))
                else:
                    result.add(State(state_index))

    return result
