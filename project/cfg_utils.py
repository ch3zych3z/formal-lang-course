from pyformlang.cfg import CFG


def to_wcnf(cfg: CFG) -> CFG:
    wcnf = cfg.eliminate_unit_productions().remove_useless_symbols()
    productions = wcnf._get_productions_with_only_single_terminals()
    productions = wcnf._decompose_productions(productions)
    return CFG(start_symbol=wcnf.start_symbol, productions=set(productions))


def from_file(path: str) -> CFG:
    with open(path, mode="r") as f:
        return CFG.from_text(f.read())
