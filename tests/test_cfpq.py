import itertools
import pytest
import networkx as nx

from project.cfpq import cfpq
from project.cfg_utils import from_file


resource_path = "tests/resources/cfg/path_query"

graphs = ["bamboo", "empty", "two_cycles"]
cfgs = ["aba_star", "bbs", "empty", "epsilon"]
algos = ["hellings", "matrix", "tensor"]

expected_results = {
    ("bamboo", "aba_star"): {("0", "3"), ("0", "2")},
    ("bamboo", "bbs"): {("1", "1"), ("0", "2"), ("0", "0"), ("2", "2"), ("3", "3")},
    ("bamboo", "empty"): set(),
    ("bamboo", "epsilon"): {("2", "2"), ("3", "3"), ("1", "1"), ("0", "0")},
    ("empty", "aba_star"): set(),
    ("empty", "bbs"): set(),
    ("empty", "empty"): set(),
    ("empty", "epsilon"): set(),
    ("two_cycles", "aba_star"): {("1", "3")},
    ("two_cycles", "bbs"): {
        ("1", "1"),
        ("0", "2"),
        ("1", "2"),
        ("0", "0"),
        ("2", "3"),
        ("2", "2"),
        ("0", "3"),
        ("1", "3"),
        ("3", "3"),
    },
    ("two_cycles", "empty"): set(),
    ("two_cycles", "epsilon"): {("2", "2"), ("3", "3"), ("1", "1"), ("0", "0")},
}


@pytest.mark.parametrize(
    "graph_name, cfg_name, algo",
    itertools.product(graphs, cfgs, algos),
)
def test_cfpq(graph_name, cfg_name, algo):
    graph = nx.drawing.nx_agraph.read_dot(f"{resource_path}/graphs/{graph_name}.dot")
    cfg = from_file(f"{resource_path}/cfgs/{cfg_name}.cfg")

    result = cfpq(cfg, graph, algorithm=algo)

    assert result == expected_results[(graph_name, cfg_name)]
