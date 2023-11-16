from networkx import MultiDiGraph
from pyformlang.cfg import CFG, Variable
from queue import SimpleQueue
from typing import Set, Tuple, Any

import project.cfg_utils as cfg_utils


def hellings_cfpq(cfg: CFG, graph: MultiDiGraph) -> Set[Tuple[Any, Variable, Any]]:
    wcnf = cfg_utils.to_wcnf(cfg)

    eps_prods = set()
    term_prods = set()
    var_prods = set()

    for production in wcnf.productions:
        body_len = len(production.body)
        if body_len == 1:
            term_prods.add(production)
        elif body_len == 2:
            var_prods.add(production)
        else:
            eps_prods.add(production)

    paths = set()

    for node in graph.nodes:
        for prod in eps_prods:
            paths.add((node, prod.head, node))

    for from_v, to_v, label in graph.edges.data("label"):
        for prod in term_prods:
            if label == prod.body[0]:
                paths.add((from_v, prod.head, to_v))

    queue = SimpleQueue()
    for r in paths:
        queue.put(r)

    def combine_paths(path1, path2):
        from_v1, var1, to_v1 = path1
        from_v2, var2, to_v2 = path2
        if to_v1 == from_v2:
            for prod in var_prods:
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


def cfpq(
    cfg: CFG,
    graph: MultiDiGraph,
    start_nodes: Set[Any] = None,
    final_nodes: Set[Any] = None,
    start_symbol: Variable = Variable("S"),
) -> Set[Tuple[Any, Variable, Any]]:
    if not start_nodes:
        start_nodes = set(graph.nodes)
    if not final_nodes:
        final_nodes = set(graph.nodes)

    paths = hellings_cfpq(cfg, graph)

    result_paths = set()
    for v1, var, v2 in paths:
        if var == start_symbol and v1 in start_nodes and v2 in final_nodes:
            result_paths.add((v1, v2))

    return result_paths
