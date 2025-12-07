
import functools
from typing import Optional
import heapq

from checker import check

def unwrap(x:tuple[int,int,int,int]|None) -> tuple[int,int,int,int]:
    assert x is not None
    return x

def pips_solver(puzzle:dict[str,list]) -> list[tuple[int,int,int,int]]:
    dominoes = puzzle['dominoes']
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
    
    def helper(
        even_spot_idx:int,
        curr_placements:list[tuple[int,int,int,int]|None],
        remaining_domino_idxs:set[int],
        remaining_spots:set[tuple[int,int]]
    ) -> Optional[list[tuple[int,int,int,int]]]:
        if not still_coverable(tuple(
            (spot in remaining_spots)
            for spot in all_spots
        )): return
        
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
        curr_spot = even_spots[even_spot_idx]
        # even remaining_spots update
        remaining_spots.remove(curr_spot)
        
        for domino_idx in list(remaining_domino_idxs):
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
                    result = helper(
                        even_spot_idx+1,
                        curr_placements,
                        remaining_domino_idxs,
                        remaining_spots
                    )
                    if result is not None:
                        return result
                    # undo curr_placements update
                    curr_placements[domino_idx] = None
                # undo odd remaining_spots update
                remaining_spots.add((curr_spot[0]+dr,curr_spot[1]+dc))
            # undo remaining_domino_idxs update
            remaining_domino_idxs.add(domino_idx)
        # undo even remaining_spots update
        remaining_spots.add(curr_spot)
    
    answer = helper(
        even_spot_idx=0,
        curr_placements=[None for _ in range(k)],
        remaining_domino_idxs=set(range(k)),
        remaining_spots=set(all_spots)
    )
    assert answer is not None
    return answer