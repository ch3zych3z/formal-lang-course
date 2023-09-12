import networkx as nx

from project.cfpq_utils import *


def test_get_graph_info():
    info = get_graph_info("skos")
    labels = list(info.labels)

    # Data from https://formallanguageconstrainedpathquerying.github.io/CFPQ_Data/graphs/data/skos.html#skos
    assert info.vertices_count == 144
    assert info.edges_count == 252
    assert len(labels) == 21


def test_write_graph_dot():
    path = "tests/graphs/generated/write_graph_dot.dot"
    n = 3
    m = 10
    labels = ("x", "y")
    graph = cfpq_data.labeled_two_cycles_graph(n, m, labels=labels)

    save_dot_labeled_two_cycles_graph(n, m, labels, path)

    written_graph = nx.nx_pydot.read_dot(path)
    assert graph.__eq__(written_graph) # for any reason (==) doesn't work properly

