from networkx import MultiDiGraph
from pyformlang.cfg import CFG, Variable, Production
from queue import SimpleQueue
from typing import Set, Tuple, Any
from dataclasses import dataclass

import project.cfg_utils as cfg_utils


@dataclass
class Productions:
    epsilon: Set[Production]
    terminal: Set[Production]
    variable: Set[Production]

    def __init__(self, cfg: CFG):
        wcnf = cfg_utils.to_wcnf(cfg)

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
            if label == prod.body[0]:
                paths.add((from_v, prod.head, to_v))

    queue = SimpleQueue()
    for r in paths:
        queue.put(r)

    def combine_paths(path1, path2):
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
                    paths.add(new_reachability)

    while not queue.empty():
        path1 = queue.get()
        for path2 in paths:
            combine_paths(path1, path2)
            combine_paths(path2, path1)

    return paths


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
