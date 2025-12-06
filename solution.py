
def pips_solver(
    board:list[list[bool]],
    dominoes: list[tuple[int,int]],
    region_rules: list[str],
    regions: list[list[int]]
) -> list[tuple[int,int,int,int]]: