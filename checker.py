
from implementations import implementations
from load_puzzles import all_puzzles

if __name__ == '__main__':
    for implementation in implementations:
        failed = False
        for puzzle_num, puzzle in enumerate(all_puzzles):
            dominoes = puzzle['dominoes']
            regions = puzzle['regions']
            solution = implementation(puzzle)

            if len(solution) != len(dominoes):
                print(f'Implementation {implementation.__name__} failed on puzzle {puzzle_num}: incorrect number of dominoes in solution, expected {len(dominoes)}, got {len(solution)}')
                failed = True
                break
                
            valid_cells = {
                spot
                for region in regions
                for spot in region['indices']
            }
            
            already_covered = set()

            for r0, c0, r1, c1 in solution:
                for spot in [(r0,c0),(r1,c1)]:
                    if spot not in valid_cells:
                        print(f'Implementation {implementation.__name__} failed on puzzle {puzzle_num}: cell {spot} is out of bounds')
                        failed = True
                        break
                    if spot in already_covered:
                        print(f'Implementation {implementation.__name__} failed on puzzle {puzzle_num}: cell {spot} is covered multiple times')
                        failed = True
                        break
                    already_covered.add(spot)
                if failed:
                    break

                if abs(c0-c1)+abs(r0-r1) != 1:
                    print(f'Implementation {implementation.__name__} failed on puzzle {puzzle_num}: domino {(r0,c0),(r1,c1)} is not placed orthogonally')
                    failed = True
                    break
            
            if failed:
                break
            
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
                        print(f'Implementation {implementation.__name__} failed on puzzle {puzzle_num}: region doesn\'t have all equal pips as required: {[spot_to_pips[spot] for spot in region["indices"]]}')
                        failed = True
                        break
                elif region['type'] == 'unequal':
                    pips_set = {
                        spot_to_pips[spot]
                        for spot in region['indices']
                    }
                    if len(pips_set) != len(region['indices']):
                        print(f'Implementation {implementation.__name__} failed on puzzle {puzzle_num}: region doesn\'t have all unequal pips as required: {[spot_to_pips[spot] for spot in region["indices"]]}')
                        failed = True
                        break
                else:
                    region_sum = sum(
                        spot_to_pips[spot]
                        for spot in region['indices']
                    )
                    if region['type'] == 'sum':
                        if region_sum != region['target']:
                            print(f'Implementation {implementation.__name__} failed on puzzle {puzzle_num}: region with target sum {region["target"]} has sum {region_sum}')
                            failed = True
                            break
                    elif region['type'] == 'less':
                        if region_sum >= region['target']:
                            print(f'Implementation {implementation.__name__} failed on puzzle {puzzle_num}: region with target less than {region["target"]} has sum {region_sum}')
                            failed = True
                            break
                    elif region['type'] == 'greater':
                        if region_sum <= region['target']:
                            print(f'Implementation {implementation.__name__} failed on puzzle {puzzle_num}: region with target greater than {region["target"]} has sum {region_sum}')
                            failed = True
                            break

            if failed:
                break
        
        if not failed:
            print(f'Implementation {implementation.__name__} passed all puzzles')