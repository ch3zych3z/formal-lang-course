import cfpq_data
from dataclasses import dataclass
from typing import Iterable, Any, Tuple

import networkx.drawing.nx_agraph


@dataclass
class GraphInfo:
    vertices_count: int
    edges_count: int
    labels: Iterable[Any]


def get_graph_info(name: str) -> GraphInfo:
    graph = cfpq_data.graph_from_csv(cfpq_data.download(name))
    return GraphInfo(
        vertices_count=graph.number_of_nodes(),
        edges_count=graph.number_of_edges(),
        labels=set(cfpq_data.get_sorted_labels(graph)),
    )


def save_dot_labeled_two_cycles_graph(
    n: int, m: int, labels: Tuple[str, str], path: str
) -> None:
    graph = cfpq_data.labeled_two_cycles_graph(n, m, labels=labels)
    networkx.drawing.nx_agraph.write_dot(graph, path)
