
import sys
import traceback

def check(
    puzzle:dict[str,list],
    solution:list[tuple[int,int,int,int]],
    print_stuff:bool,
    implementation_name=None,
    puzzle_num=None
) -> bool:
    dominoes = puzzle['dominoes']
    regions = puzzle['regions']

    if len(solution) != len(dominoes):
        if print_stuff:
            print(f'Implementation {implementation_name} failed on puzzle {puzzle_num}: incorrect number of dominoes in solution, expected {len(dominoes)}, got {len(solution)}')
        return False
        
    valid_cells = {
        spot
        for region in regions
        for spot in region['indices']
    }
    
    already_covered = set()

    for r0, c0, r1, c1 in solution:
        for spot in [(r0,c0),(r1,c1)]:
            if spot not in valid_cells:
                if print_stuff:
                    print(f'Implementation {implementation_name} failed on puzzle {puzzle_num}: cell {spot} is out of bounds')
                return False
            if spot in already_covered:
                if print_stuff:
                    print(f'Implementation {implementation_name} failed on puzzle {puzzle_num}: cell {spot} is covered multiple times')
                return False
            already_covered.add(spot)

        if abs(c0-c1)+abs(r0-r1) != 1:
            if print_stuff:
                print(f'Implementation {implementation_name} failed on puzzle {puzzle_num}: domino {(r0,c0),(r1,c1)} is not placed orthogonally')
            return False
    
    spot_to_pips = {}
    for (pips1, pips2), (r0, c0, r1, c1) in zip(dominoes, solution):
        spot_to_pips[r0,c0] = pips1
        spot_to_pips[r1,c1] = pips2
    
    for region in regions:
        if region['type'] == 'equals':
            target = spot_to_pips[region['indices'][0]]
            if not all(
                spot_to_pips[spot] == target
                for spot in region['indices']
            ):
                if print_stuff:
                    print(f'Implementation {implementation_name} failed on puzzle {puzzle_num}: region doesn\'t have all equal pips as required: {[spot_to_pips[spot] for spot in region["indices"]]}')
                return False
        elif region['type'] == 'unequal':
            pips_set = {
                spot_to_pips[spot]
                for spot in region['indices']
            }
            if len(pips_set) != len(region['indices']):
                if print_stuff:
                    print(f'Implementation {implementation_name} failed on puzzle {puzzle_num}: region doesn\'t have all unequal pips as required: {[spot_to_pips[spot] for spot in region["indices"]]}')
                return False
        else:
            region_sum = sum(
                spot_to_pips[spot]
                for spot in region['indices']
            )
            if region['type'] == 'sum':
                if region_sum != region['target']:
                    if print_stuff:
                        print(f'Implementation {implementation_name} failed on puzzle {puzzle_num}: region with target sum {region["target"]} has sum {region_sum}')
                    return False
            elif region['type'] == 'less':
                if region_sum >= region['target']:
                    if print_stuff:
                        print(f'Implementation {implementation_name} failed on puzzle {puzzle_num}: region with target less than {region["target"]} has sum {region_sum}')
                    return False
            elif region['type'] == 'greater':
                if region_sum <= region['target']:
                    if print_stuff:
                        print(f'Implementation {implementation_name} failed on puzzle {puzzle_num}: region with target greater than {region["target"]} has sum {region_sum}')
                    return False
    
    return True

if __name__ == '__main__':
    from implementations import implementations
    from load_puzzles import all_puzzles

    for implementation_num, implementation in enumerate(implementations):
        failed = False
        for puzzle_num, puzzle in enumerate(all_puzzles):
            try:
                solution = implementation(puzzle)
            except Exception as e:
                print(f'Implementation {implementation_num} failed on puzzle {puzzle_num} with {type(e).__name__} exception:')
                traceback.print_exc(file=sys.stdout)
                failed = True
                break
            if not check(
                puzzle,
                solution,
                print_stuff=True,
                implementation_name=implementation_num,
                puzzle_num=puzzle_num
            ):
                failed = True
                break
            print(f'Implementation {implementation_num} passed puzzle {puzzle_num}')
        
        if not failed:
            print(f'Implementation {implementation_num} passed all puzzles')