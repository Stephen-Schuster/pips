
import functools
from typing import Optional
import heapq

from checker import check

def unwrap(x:tuple[int,int,int,int]|None) -> tuple[int,int,int,int]:
    assert x is not None
    return x

def pips_solver(puzzle:dict[str,list]) -> list[tuple[int,int,int,int]]:
    dominoes = puzzle['dominoes']
    regions = puzzle['regions']
    k = len(dominoes)
    all_spots = sorted(
        spot
        for region in puzzle['regions']
        for spot in region['indices']
    )

    even_spots = [
        spot for spot in all_spots
        if (spot[0]+spot[1])%2 == 0
    ]
    assert len(even_spots) == k

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
    
    curr_placements:list[tuple[int,int,int,int]|None]=[None for _ in range(k)]
    remaining_domino_idxs:set[int]=set(range(k))
    remaining_spots:set[tuple[int,int]]=set(all_spots)
    spots_to_pips:dict[tuple[int,int],int]={}

    def region_rules_violated() -> bool:
        for region in regions:
            if region['type'] == 'unequal':
                seen = set()
                for spot in region['indices']:
                    if spot in spots_to_pips:
                        pip_ct = spots_to_pips[spot]
                        if pip_ct in seen:
                            return True
                        seen.add(pip_ct)
            elif region['type'] == 'equal':
                target = None
                for spot in region['indices']:
                    if spot in spots_to_pips:
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
                elif region['type'] == 'less':
                    if curr_sum >= region['target']:
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
        # if sum(sorted_pip_counts[:leq_spots]) > leq_total:
        #     return False
        
        return True

    def helper(even_spot_idx:int) -> Optional[list[tuple[int,int,int,int]]]:
        nonlocal curr_placements
        nonlocal remaining_domino_idxs
        nonlocal remaining_spots
        nonlocal spots_to_pips
        
        if even_spot_idx >= k:
            final_placements:list[tuple[int,int,int,int]] = [unwrap(x) for x in curr_placements]
            is_valid = check(
                puzzle,
                final_placements,
                print_stuff=False
            )
            if is_valid:
                return final_placements
            else:
                return

        if region_rules_violated():
            return

        if not regions_still_possible():
            return
        
        if not still_coverable(tuple(
            (spot in remaining_spots)
            for spot in all_spots
        )): return

        curr_spot = even_spots[even_spot_idx]
        # even remaining_spots update
        remaining_spots.remove(curr_spot)
        
        for domino_idx in list(remaining_domino_idxs):
            curr_domino = dominoes[domino_idx]
            # remaining_domino_idxs update
            remaining_domino_idxs.remove(domino_idx)
            directions = [(1,0),(0,1),(-1,0),(0,-1)]
            for dr, dc in directions:
                if (curr_spot[0]+dr,curr_spot[1]+dc) not in remaining_spots:
                    continue
                # odd remaining_spots update
                remaining_spots.remove((curr_spot[0]+dr,curr_spot[1]+dc))
                for (r0,c0,r1,c1) in [
                    (*curr_spot,curr_spot[0]+dr,curr_spot[1]+dc),
                    (curr_spot[0]+dr,curr_spot[1]+dc,*curr_spot)
                ]:
                    # curr_placements update
                    curr_placements[domino_idx] = (r0,c0,r1,c1)
                    # spots_to_pips update
                    spots_to_pips[r0,c0] = curr_domino[0]
                    spots_to_pips[r1,c1] = curr_domino[1]
                    result = helper(even_spot_idx+1)
                    if result is not None:
                        return result
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
    
    answer = helper(0)
    assert answer is not None
    return answer