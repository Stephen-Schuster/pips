
import functools
from typing import Optional
import heapq

from checker import check
from solve_fast_propagation import solve_fast_propagation
    
# domino index, domino half index (0/1), dr, dc
type Possibility = tuple[int,int,int,int]

# r0, c0, r1, c1
type Placement = tuple[int,int,int,int]

def unwrap(x):
    assert x is not None
    return x

def reduce_possibilities(
    possibilities:list[set[Possibility]]
) -> bool:
    # domains = {
    #     idx: {domino_idx for domino_idx,_,_,_ in possibility_set}
    #     for idx, possibility_set in enumerate(possibilities)
    # }
    domains = solve_fast_propagation(tuple(
        frozenset(
            domino_idx
            for domino_idx,_,_,_
            in possibility_set
        )
        for possibility_set in possibilities
    ))
    if domains is not None:
        for idx in range(len(possibilities)):
            allowed_dominoes = domains[idx]
            possibilities[idx].intersection_update({
                p for p in possibilities[idx]
                if p[0] in allowed_dominoes
            })
    return domains is not None

def contradiction_found(
    possibilities:list[set[Possibility]]
) -> bool:
    return any(
        len(possibility_set) == 0
        for possibility_set in possibilities
    )

def place_domino(
    possibilities:list[set[Possibility]],
    possibility_idx:int,
    possibility: Possibility
) -> list[set[Possibility]]:
    return [
        (
            {possibility}
            if i == possibility_idx
            else {
                p for p in possibility_set
                if p[0] != possibility[0]
            }
        )
        for i, possibility_set in enumerate(possibilities)
    ]

def pips_solver(puzzle:dict[str,list]) -> list[Placement]:
    calls = 0
    dominoes = puzzle['dominoes']
    regions = puzzle['regions']
    k = len(dominoes)
    all_spots = sorted(
        spot
        for region in puzzle['regions']
        for spot in region['indices']
    )
    all_spots_set = set(all_spots)
    even_spots = [
        spot for spot in all_spots
        if (spot[0]+spot[1])%2 == 0
    ]
    assert len(even_spots) == k

    spot_to_region = {
        spot: region
        for region in regions
        for spot in region['indices']
    }
    spot_to_even_idx = {
        spot: idx
        for idx, spot in enumerate(even_spots)
    }

    @functools.cache
    def still_coverable(spot_still_available:tuple[bool,...]) -> bool:
        spots_left = {
            spot for available, spot in zip(spot_still_available,all_spots)
            if available
        }
        if len(spots_left) == 0:
            return True
        one_neighbor_spot:Optional[tuple[int,int]] = None
        two_neighbor_spot:Optional[tuple[int,int]] = None
        three_neighbor_spot:Optional[tuple[int,int]] = None
        four_neighbor_spot:Optional[tuple[int,int]] = None

        def get_neighbors(r,c):
            return [
                spot for spot in [
                    (r+1,c),
                    (r-1,c),
                    (r,c+1),
                    (r,c-1),
                ]
                if spot in spots_left
            ]
        
        for r,c in sorted(spots_left):
            num_neighbors = len(get_neighbors(r,c))

            if num_neighbors == 0: 
                return False
            elif num_neighbors == 1:
                one_neighbor_spot = (r,c)
                break
            elif num_neighbors == 2 and two_neighbor_spot is None:
                two_neighbor_spot = (r,c)
            elif num_neighbors == 3 and three_neighbor_spot is None:
                three_neighbor_spot = (r,c)
            elif num_neighbors == 4 and four_neighbor_spot is None:
                four_neighbor_spot = (r,c)

        if one_neighbor_spot is not None:
            to_try = [
                (one_neighbor_spot,neighbor) 
                for neighbor in get_neighbors(*one_neighbor_spot)
            ]
        elif two_neighbor_spot is not None:
            to_try = [
                (two_neighbor_spot,neighbor) 
                for neighbor in get_neighbors(*two_neighbor_spot)
            ]
        elif three_neighbor_spot is not None:
            to_try = [
                (three_neighbor_spot,neighbor) 
                for neighbor in get_neighbors(*three_neighbor_spot)
            ]
        elif four_neighbor_spot is not None:
            to_try = [
                (four_neighbor_spot,neighbor) 
                for neighbor in get_neighbors(*four_neighbor_spot)
            ]
        else:
            raise RuntimeError('how tf')
        
        # order to_try
        def least_neighbors_neighbors(spot_pair:tuple[tuple[int,int],tuple[int,int]])->int:
            og, neighbor = spot_pair
            return min([
                    len(get_neighbors(*neighbor_neighbor))
                    for neighbor_neighbor in get_neighbors(*neighbor)
                    if neighbor_neighbor != og
                ],
                default=0
            )
        to_try.sort(key=least_neighbors_neighbors)
        
        for spot_pair in to_try:
            if still_coverable(tuple(
                (
                    available and 
                    spot not in spot_pair
                )
                for available, spot in zip(spot_still_available,all_spots)
            )): return True
        return False
    
    curr_placements:list[Placement|None]=[None for _ in range(k)]
    remaining_domino_idxs:set[int]=set(range(k))
    remaining_spots:set[tuple[int,int]]=set(all_spots)
    spots_to_pips:dict[tuple[int,int],int]={}
    
    def all_possibilities() -> set[Placement]:
        return {
            (idx, half_idx, dr, dc)
            for idx in range(k)
            for half_idx in [0,1]
            for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]
        }

    def region_rules_violated(print_stuff=False) -> bool:
        for region in regions:
            if print_stuff: print(region['type'],region['indices'])
            if region['type'] == 'unequal':
                seen = set()
                for spot in region['indices']:
                    if spot in spots_to_pips:
                        pip_ct = spots_to_pips[spot]
                        if pip_ct in seen:
                            return True
                        seen.add(pip_ct)
            elif region['type'] == 'equals':
                target = None
                for spot in region['indices']:
                    if spot in spots_to_pips:
                        if print_stuff:
                            print(spot,spots_to_pips[spot],target)
                        if target is None:
                            target = spots_to_pips[spot]
                        elif spots_to_pips[spot] != target:
                            return True
            elif region['type'] == 'sum' or region['type'] == 'less':
                curr_sum = sum(
                    spots_to_pips.get(spot,0)
                    for spot in region['indices']
                )
                if region['type'] == 'sum':
                    if curr_sum > region['target']:
                        return True
                    unfilled_spots = sum(1 for spot in region['indices'] if spot in remaining_spots)
                    if curr_sum + unfilled_spots * 6 < region['target']:
                        return True
                elif region['type'] == 'less':
                    if curr_sum >= region['target']:
                        return True
                elif region['type'] == 'greater':
                    if all(
                        (spot in spots_to_pips)
                        for spot in region['indices']
                    ) and curr_sum <= region['target']:
                            return True
        return False

    def regions_still_possible() -> bool:
        pips_to_count = {x:0 for x in range(7)}
        for idx in remaining_domino_idxs:
            pips1, pips2 = dominoes[idx]
            pips_to_count[pips1] += 1
            pips_to_count[pips2] += 1
        
        # equals with filled targets
        for region in regions:
            if region['type'] == 'equals':
                unfilled_count = 0
                target = None
                for spot in region['indices']:
                    if spot in spots_to_pips:
                        target = spots_to_pips[spot]
                    else:
                        unfilled_count += 1
                if target is not None:
                    if pips_to_count[target] < unfilled_count:
                        return False
                    pips_to_count[target] -= unfilled_count
        
        # single cell remaining sums
        for region in regions:
            if region['type'] == 'sum':
                unfilled_count = 0
                curr_sum = 0
                for spot in region['indices']:
                    if spot not in spots_to_pips:
                        unfilled_count += 1
                    else:
                        curr_sum += spots_to_pips[spot]
                if unfilled_count == 1:
                    target = region['target'] - curr_sum
                    if not (0 <= target <= 6):
                        return False
                    if pips_to_count[target] < 1:
                        return False
                    pips_to_count[target] -= 1
        
        # make sure remaining sum is sufficient
        remaining_sum = sum(
            p * c
            for p, c in pips_to_count.items()
        )
        remaining_min_sum = 0 # not counting single cell remaining sums
        remaining_non_sum_squares = 0 # not counting equals with filled targets
        for region in regions:
            if region['type'] == 'sum':
                unfilled_count = sum(1 for spot in region['indices'] if spot not in spots_to_pips)
                if unfilled_count == 1: continue
                change = region['target'] - sum(spots_to_pips.get(spot,0) for spot in region['indices'])
                if change < 0:
                    return False
                remaining_min_sum += change
            elif region['type'] == 'greater':
                change = region['target']+1 - sum(spots_to_pips.get(spot,0) for spot in region['indices'])
                if change > 0: 
                    remaining_min_sum += change
            else:
                if region['type'] == 'equals' and any((spot in spots_to_pips) for spot in region['indices']):
                    continue
                remaining_non_sum_squares += sum(
                    1 for spot in region['indices']
                    if spot in remaining_spots
                )
        sorted_pip_counts = sorted(
            p for p, c in pips_to_count.items()
            for _ in range(c)
        )
        remaining_min_sum += sum(sorted_pip_counts[:remaining_non_sum_squares])
        if remaining_min_sum > remaining_sum:
            return False
        
        highest_count = max(pips_to_count.values())
        leq_total = 0
        leq_spots = 0
        for region in regions:
            # equals with unfilled targets
            if region['type'] == 'equals':
                unfilled_count = 0
                target = None
                for spot in region['indices']:
                    if spot in spots_to_pips:
                        target = spots_to_pips[spot]
                    else:
                        unfilled_count += 1
                if target is None and unfilled_count > highest_count:
                    return False
            
            # unequal regions
            elif region['type'] == 'unequal':
                seen = {spots_to_pips[spot] for spot in region['indices'] if spot in spots_to_pips}
                num_spots_to_fill = len(region['indices']) - len(seen)
                num_unseen = sum(1 for p, c in pips_to_count.items() if c > 0 and p not in seen)
                if num_spots_to_fill > num_unseen:
                    return False
            
            # less regions
            elif region['type'] == 'less':
                max_to_add = region['target'] - sum(
                    spots_to_pips.get(spot,0)
                    for spot in region['indices']
                ) - 1
                spaces_remaining = sum(
                    1 for spot in region['indices']
                    if spot in remaining_spots
                )
                if max_to_add < 0:
                    return False
                leq_total += max_to_add
                leq_spots += spaces_remaining
        if sum(sorted_pip_counts[:leq_spots]) > leq_total:
            return False
        
        return True

    def still_valid() -> bool:
        return (
            not region_rules_violated() and
            regions_still_possible() and
            still_coverable(tuple(
                (spot in remaining_spots)
                for spot in all_spots
            ))
        )
    
    def done() -> bool:
        assert (
            all(x is not None for x in curr_placements) ==
            (len(remaining_domino_idxs) == 0) ==
            (len(remaining_spots) == 0) ==
            (len(spots_to_pips) == 2*k)
        )
        return len(remaining_domino_idxs) == 0

    def get_next_spot(possibilities:list[set[Possibility]]) -> int:
        # first prioritize single possibility spots
        for idx, possibility_set in enumerate(possibilities):
            if even_spots[idx] in remaining_spots and len(possibility_set) == 1:
                return idx
        # then prioritize nonempty regions with the least unfilled spots
        # then prioritize spots with the least possibilities
        spot_to_possibility_count = {
            even_spots[even_spot_idx]: len(possibility_set)
            for even_spot_idx, possibility_set in enumerate(possibilities)
        }
        best = None
        for region in regions:
            unfilled_spots = [
                spot for spot in region['indices']
                if spot in remaining_spots
            ]
            for spot in unfilled_spots:
                if spot not in spot_to_possibility_count:
                    continue
                pref_key = (region['type'] == 'empty', len(unfilled_spots), spot_to_possibility_count[spot])
                if best is None or pref_key < best[1]:
                    best = (spot_to_even_idx[spot], pref_key)
        assert best is not None
        return best[0]

    
    def remove_impossibilities(
        possibilities:list[set[Possibility]]
    ) -> None:
        # edit in place
        for even_spot_idx, possibility_set in enumerate(possibilities):
            even_spot = even_spots[even_spot_idx]
            for possibility in list(possibility_set):
                domino_idx, half_idx, dr, dc = possibility
                if domino_idx not in remaining_domino_idxs:
                    continue
                odd_spot = (even_spot[0]+dr, even_spot[1]+dc)

                # placed out of bounds
                if odd_spot not in all_spots_set:
                    possibility_set.remove(possibility)
                    continue

                # placed overlapping with existing domino
                if (
                    even_spot not in remaining_spots or
                    odd_spot not in remaining_spots
                ):
                    possibility_set.remove(possibility)
                    continue

                # breaks a region rule
                even_pips = dominoes[domino_idx][half_idx]
                odd_pips = dominoes[domino_idx][1 - half_idx]
                for spot, pips in [(even_spot, even_pips), (odd_spot, odd_pips)]:
                    region = spot_to_region[spot]
                    if region['type'] == 'equals':
                        if any(
                            spots_to_pips.get(s, pips) != pips
                            for s in region['indices']
                        ):
                            possibility_set.remove(possibility)
                            break
                    elif region['type'] == 'unequal':
                        distinct_pips = {pips}
                        bad = False
                        for s in region['indices']:
                            if s in spots_to_pips:
                                if spots_to_pips[s] in distinct_pips:
                                    possibility_set.remove(possibility)
                                    bad = True
                                    break
                                distinct_pips.add(spots_to_pips[s])
                        if bad:
                            break
                    else:
                        region_sum = sum(
                            spots_to_pips.get(s,0)
                            for s in region['indices']
                        ) + pips
                        if region['type'] == 'sum':
                            if region_sum > region['target']:
                                possibility_set.remove(possibility)
                                break
                            unfilled_spots = sum(1 for s in region['indices'] if s in remaining_spots and s != spot)
                            if region_sum + unfilled_spots * 6 < region['target']:
                                possibility_set.remove(possibility)
                                break
                        elif region['type'] == 'less':
                            if region_sum >= region['target']:
                                possibility_set.remove(possibility)
                                break
                        elif region['type'] == 'greater':
                            unfilled_spots = sum(1 for s in region['indices'] if s in remaining_spots and s != spot)
                            if region_sum + unfilled_spots * 6 <= region['target']:
                                possibility_set.remove(possibility)
                                break

    def helper(possibilities:list[set[Possibility]]) -> Optional[list[Placement]]:
        nonlocal curr_placements
        nonlocal remaining_domino_idxs
        nonlocal remaining_spots
        nonlocal spots_to_pips
        nonlocal calls
        calls += 1
        # if calls % 10_000 == 0:
        #     print(f'{calls} calls made so far...')
        #     print(f'Remaining dominoes: {[dominoes[idx] for idx in remaining_domino_idxs]}')
        #     grid_width = max(c for r,c in all_spots)+1
        #     grid_height = max(r for r,c in all_spots)+1
        #     print(f'Current grid({grid_width}x{grid_height}):')
        #     for r in range(grid_height):
        #         for c in range(grid_width):
        #             if (r,c) in spots_to_pips:
        #                 print(spots_to_pips[r,c], end=' ')
        #             elif (r,c) in remaining_spots:
        #                 print('.', end=' ')
        #             else:
        #                 print(' ', end=' ')
        #         print()
        #     # print('region rules violated?',region_rules_violated(True))
        #     # raise

        if done():
            final_placements:list[tuple[int,int,int,int]] = [unwrap(x) for x in curr_placements]
            if check(
                puzzle,
                final_placements,
                print_stuff=False
            ):
                return final_placements
            else:
                return

        remove_impossibilities(possibilities)
        success = reduce_possibilities(possibilities)
        if not success:
            return
        if contradiction_found(possibilities):
            return
        
        next_spot_idx = get_next_spot(possibilities)       

        if not still_valid():
            return
        
        curr_spot = even_spots[next_spot_idx]

        # even remaining_spots update
        remaining_spots.remove(curr_spot)
        for domino_idx, half_idx, dr, dc in list(possibilities[next_spot_idx]):
            curr_domino = dominoes[domino_idx]
            # remaining_domino_idxs update
            remaining_domino_idxs.remove(domino_idx)
            # odd remaining_spots update
            remaining_spots.remove((curr_spot[0]+dr,curr_spot[1]+dc))

            if half_idx == 0:
                r0, c0 = curr_spot
                r1, c1 = curr_spot[0]+dr, curr_spot[1]+dc
            else:
                r1, c1 = curr_spot
                r0, c0 = curr_spot[0]+dr, curr_spot[1]+dc
            # curr_placements update
            curr_placements[domino_idx] = (r0,c0,r1,c1)
            # spots_to_pips update
            spots_to_pips[r0,c0] = curr_domino[0]
            spots_to_pips[r1,c1] = curr_domino[1]
            
            result = helper(
                place_domino(
                    possibilities,
                    next_spot_idx,
                    (domino_idx, half_idx, dr, dc)
                )
            )
            if result is not None:
                return result
            possibilities[next_spot_idx].remove((domino_idx, half_idx, dr, dc))

            # undo curr_placements update
            curr_placements[domino_idx] = None
            # undo spots_to_pips update
            del spots_to_pips[r0,c0]
            del spots_to_pips[r1,c1]
            # undo odd remaining_spots update
            remaining_spots.add((curr_spot[0]+dr,curr_spot[1]+dc))
            # undo remaining_domino_idxs update
            remaining_domino_idxs.add(domino_idx)
        # undo even remaining_spots update
        remaining_spots.add(curr_spot)
    
    answer = helper([
        all_possibilities()
        for _ in range(k)
    ])
    # print(calls, "calls made during solving")
    return unwrap(answer)