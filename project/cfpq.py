from networkx import MultiDiGraph
from pyformlang.cfg import CFG, Variable, Production
from queue import SimpleQueue
from typing import Set, Tuple, Any
from dataclasses import dataclass
from scipy.sparse import dok_array, eye, lil_matrix

import project.cfg_utils as cfg_utils
from project.ecfg import Ecfg
from project.rsm import Rsm
import project.automata_utils as au


@dataclass
class Productions:
    epsilon: Set[Production]
    terminal: Set[Production]
    variable: Set[Production]
    wcnf: CFG

    def __init__(self, cfg: CFG):
        wcnf = cfg_utils.to_wcnf(cfg)

        self.wcnf = wcnf
        self.epsilon = set()
        self.terminal = set()
        self.variable = set()

        for production in wcnf.productions:
            body_len = len(production.body)
            if body_len == 1:
                self.terminal.add(production)
            elif body_len == 2:
                self.variable.add(production)
            else:
                self.epsilon.add(production)


def _hellings_cfpq(cfg: CFG, graph: MultiDiGraph) -> Set[Tuple[Any, Variable, Any]]:
    prods = Productions(cfg)

    paths = set()

    for node in graph.nodes:
        for prod in prods.epsilon:
            paths.add((node, prod.head, node))

    for from_v, to_v, label in graph.edges.data("label"):
        for prod in prods.terminal:
            if label == prod.body[0].value:
                paths.add((from_v, prod.head, to_v))

    queue = SimpleQueue()
    for r in paths:
        queue.put(r)

    def combine_paths(path1, path2, new_paths):
        from_v1, var1, to_v1 = path1
        from_v2, var2, to_v2 = path2
        if to_v1 == from_v2:
            for prod in prods.variable:
                new_reachability = (from_v1, prod.head, to_v2)
                if (
                    prod.body[0] == var1
                    and prod.body[1] == var2
                    and new_reachability not in paths
                ):
                    queue.put(new_reachability)
                    new_paths.add(new_reachability)

    while not queue.empty():
        new_paths = set()
        path1 = queue.get()
        for path2 in paths:
            combine_paths(path1, path2, new_paths)
            combine_paths(path2, path1, new_paths)
        paths |= new_paths

    return paths


def _matrix_cfpq(cfg: CFG, graph: MultiDiGraph) -> Set[Tuple[Any, Variable, Any]]:
    prods = Productions(cfg)

    var_to_mtx = {}
    nodes = list(graph.nodes)
    node_index = dict([(node, i) for i, node in enumerate(nodes)])

    n = graph.number_of_nodes()
    for var in prods.wcnf.variables:
        var_to_mtx[var] = lil_matrix((n, n), dtype=bool)

    for i, node in enumerate(graph.nodes):
        for prod in prods.epsilon:
            var_to_mtx[prod.head][i, i] = True

    for from_, to, label in graph.edges(data="label"):
        for prod in prods.terminal:
            if label == prod.body[0].value:
                from_index = node_index[from_]
                to_index = node_index[to]
                var_to_mtx[prod.head][from_index, to_index] = True

    while True:
        new_paths_found = False
        for prod in prods.variable:
            previous_nonzero_count = var_to_mtx[prod.head].count_nonzero()
            assert isinstance(prod.body[0], Variable)
            assert isinstance(prod.body[1], Variable)
            var_to_mtx[prod.head] += var_to_mtx[prod.body[0]] @ var_to_mtx[prod.body[1]]

            new_paths_found |= (
                previous_nonzero_count != var_to_mtx[prod.head].count_nonzero()
            )

        if not new_paths_found:
            break

    reachabilities = set()
    for variable, matrix in var_to_mtx.items():
        rows, cols = matrix.nonzero()
        for i in range(len(rows)):
            row_index = rows[i]
            col_index = cols[i]
            reachabilities.add((nodes[row_index], variable, nodes[col_index]))

    return reachabilities


def _tensor_cfpq(cfg: CFG, graph: MultiDiGraph) -> Set[Tuple[Any, Variable, Any]]:
    bmatrix_rsm = au.BooleanDecomposition.from_fa(
        Rsm.from_ecfg(Ecfg.from_cfg(cfg)).minimize().merge_boxes()
    )

    bmatrix_graph = au.BooleanDecomposition.from_fa(au.nfa_from_graph(graph))
    graph_states_count = len(bmatrix_graph.states)

    identity_matrix = eye(graph_states_count, format="dok", dtype=bool)
    for nonterm in cfg.get_nullable_symbols():
        if nonterm.value in bmatrix_graph.labels:
            bmatrix_graph[nonterm.value] += identity_matrix
        else:
            bmatrix_graph[nonterm.value] = identity_matrix

    new_paths_found = True
    last_iteration_nnz = 0
    while new_paths_found:
        tc_indexes = list(
            zip(
                *au.transitive_closure_boolean(
                    au.intersect_boolean(bmatrix_rsm, bmatrix_graph)
                ).nonzero()
            )
        )
        new_paths_found &= last_iteration_nnz != len(tc_indexes)
        last_iteration_nnz = len(tc_indexes)

        for i_from, i_to in tc_indexes:
            rsm_from, graph_from = divmod(i_from, graph_states_count)
            rsm_to, graph_to = divmod(i_to, graph_states_count)

            state_from = bmatrix_rsm.states[rsm_from]
            state_to = bmatrix_rsm.states[rsm_to]
            nonterm, _ = state_from.value
            if (
                state_from in bmatrix_rsm.start_states
                and state_to in bmatrix_rsm.final_states
            ):
                if nonterm.value in bmatrix_graph.labels:
                    bmatrix_graph[nonterm.value][graph_from, graph_to] = True
                else:
                    bmatrix_graph[nonterm.value] = lil_matrix(
                        (
                            graph_states_count,
                            graph_states_count,
                        ),
                        dtype=bool,
                    )
                    bmatrix_graph[nonterm.value][graph_from, graph_to] = True
    return {
        (
            bmatrix_graph.states[graph_from],
            nonterm,
            bmatrix_graph.states[graph_to],
        )
        for nonterm, matrix in bmatrix_graph.items
        for graph_from, graph_to in zip(*matrix.nonzero())
    }


def _cfpq(
    cfg: CFG,
    graph: MultiDiGraph,
    algo,
    start_nodes: Set[Any] = None,
    final_nodes: Set[Any] = None,
    start_symbol: Variable = Variable("S"),
) -> Set[Tuple[Any, Any]]:
    if not start_nodes:
        start_nodes = set(graph.nodes)
    if not final_nodes:
        final_nodes = set(graph.nodes)

    paths = algo(cfg, graph)

    result_paths = set()
    for v1, var, v2 in paths:
        if var == start_symbol and v1 in start_nodes and v2 in final_nodes:
            result_paths.add((v1, v2))

    return result_paths


_algos = {
    "hellings": _hellings_cfpq,
    "matrix": _matrix_cfpq,
    "tensor": _tensor_cfpq,
}


def cfpq(
    cfg: CFG,
    graph: MultiDiGraph,
    algorithm: str,
    start_nodes: Set[Any] = None,
    final_nodes: Set[Any] = None,
    start_symbol: Variable = Variable("S"),
) -> Set[Tuple[Any, Any]]:
    algo = _algos[algorithm]
    return _cfpq(cfg, graph, algo, start_nodes, final_nodes, start_symbol)
