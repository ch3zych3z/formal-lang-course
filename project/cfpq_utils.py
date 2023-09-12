import cfpq_data
from dataclasses import dataclass
from typing import Iterable, Any, TextIO, Tuple
from networkx import MultiDiGraph
from networkx.drawing.nx_pydot import to_pydot


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
        labels=set(cfpq_data.get_sorted_labels(graph))
    )


def write_graph_dot(graph: MultiDiGraph, f: TextIO) -> None:
    dot = to_pydot(graph).to_string()
    f.write(dot)


def save_dot_labeled_two_cycles_graph(n: int, m: int, labels: Tuple[str, str], path: str) -> None:
    graph = cfpq_data.labeled_two_cycles_graph(n, m, labels=labels)
    with open(path, 'w') as f:
        write_graph_dot(graph, f)
