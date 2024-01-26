from antlr4 import (
    CommonTokenStream,
    InputStream,
    ParseTreeWalker,
    ParserRuleContext,
    TerminalNode,
)

from project.graph_query_lang.langListener import langListener
from project.graph_query_lang.langParser import langParser
from project.graph_query_lang.langLexer import langLexer
from pydot import Dot, Edge, Node


def parse(text: str) -> "langParser":
    stream = InputStream(text)
    lexer = langLexer(stream)
    tokens = CommonTokenStream(lexer)

    return langParser(tokens)


def check_ast(text: str) -> bool:
    parser = parse(text)
    parser.prog()

    result: bool = parser.getNumberOfSyntaxErrors() == 0
    return result


def save_dot(parser: "langParser", path: str):
    tree = parser.prog()

    if parser.getNumberOfSyntaxErrors() > 0:
        raise ValueError("Ahtung! Given parser contains errors")

    listener = DotTreeListener()
    walker = ParseTreeWalker()
    walker.walk(listener, tree)

    if not listener.dot.write(path):
        raise RuntimeError(f"Unable to save to {path}!")


class DotTreeListener(langListener):
    def __init__(self):
        self.dot = Dot("ast", strict=True)
        self.curr = 0
        self.stack = []

    def enterEveryRule(self, ctx: ParserRuleContext):
        self.dot.add_node(
            Node(self.curr, label=langParser.ruleNames[ctx.getRuleIndex()])
        )

        if len(self.stack) > 0:
            self.dot.add_edge(Edge(self.stack[-1], self.curr))

        self.stack += [self.curr]
        self.curr += 1

    def exitEveryRule(self, ctx: ParserRuleContext):
        self.stack.pop()

    def visitTerminal(self, node: TerminalNode):
        self.dot.add_node(Node(self.curr, label=f"'{node}'", shape="box"))
        self.dot.add_edge(Edge(self.stack[-1], self.curr))
        self.curr += 1
