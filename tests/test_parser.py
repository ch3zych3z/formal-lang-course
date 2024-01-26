import os.path
from os import path
import pytest
import filecmp

from project.graph_query_lang.parser import check_ast, save_dot, parse

PATH = path.dirname(path.realpath(__file__))

true_positive_tests = [
    "let x = x",
    "let x = _x",
    "let x = X",
    "let x = _som123e_vaR123",
    "let x = 1",
    "let x = 0",
    "let x = -1",
    "let x = true",
    "let x = false",
    'let x = {"a* (b | c)"}',
    "let x = {|S -> S b |}",
    "let x = g |> set_start [4, 2]",
    "let x = g |> set_final [4, 2]",
    "let x = g |> add_start [4, 2]",
    "let x = g |> add_final [4, 2]",
    "let x = get_start g",
    "let x = get_final g",
    "let x = (get_reachable g)",
    "let x = get_vertices g",
    "let x = s |> map (\\v -> 1)",
    "let x = [1, 2] |> filter (\\i -> false)",
    "let x = [3, 4] |> filter (\\i -> i in [2,3])",
    "let x = []",
    "let x = [1]",
    "let x = [2, 4, 5, 6]",
    "let x = a in b",
    "let x = a*",
    "print 1",
    "\n\n\nprint 1\n\nprint 42\n",
]

true_negative_tests = [
    "let x = 1x",
    "let 1x = 1x",
    "let x = 023423",
    "let x = 0000",
    "let x = set_start [4, 2] g",
    "let x = set_final [4, 2]",
    "let x = [2 2 8]",
    "let x = a * b",
    "let x = map(\\_ -> 1)",
    "let x = filter(\\_ -> false)",
    "let x = load",
    "let x = [4, 2] |> map (\\1 -> false)",
    "let x = 1 2",
    "x y z = 1",
    "print(1, 2, 3)",
    "print 1 2 3",
]


@pytest.mark.parametrize(
    "s",
    [test for test in true_positive_tests],
)
def test_true_positive(s: str):
    assert check_ast(s)


@pytest.mark.parametrize(
    "s",
    [test for test in true_negative_tests],
)
def test_true_negative(s: str):
    assert not check_ast(s)


test_script = """
let gr = load "filename"
let vertices = get_vertices gr
let gr = gr |> set_start vertices |> set_final [0..3]

let regex1 = {"a+"}
let regex2 = {"b*"}
let regex = regex1 | regex2

let cfg = {| S -> a S b S | S -> epsilon |}

let regex_intersection = graph & regex
print regex_intersection

let cfg_intersection = graph & cfg
print cfg_intersection
"""


def test_save_dot():
    actual_path = os.path.join(PATH, "resources", "parser", "actual.dot")
    expected_path = os.path.join(PATH, "resources", "parser", "expected.dot")

    parser = parse(test_script)
    save_dot(parser, actual_path)

    assert filecmp.cmp(actual_path, expected_path)
    os.remove(actual_path)
