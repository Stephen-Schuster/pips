
from typing import Optional
import heapq

from checker import check


def pips_solver(puzzle:dict[str,list]) -> list[tuple[int,int,int,int]]:
    dominoes = puzzle['dominoes']

    def helper(
        domino_idx:int,
        curr_placements:list[tuple[int,int,int,int]],
        remaining_spots:set[tuple[int,int]]
    ) -> Optional[list[tuple[int,int,int,int]]]:
        if domino_idx >= len(dominoes):
            is_valid = check(
                puzzle,
                curr_placements,
                print_stuff=False
            )
            # print(curr_placements,is_valid)
            if is_valid:
                return curr_placements
            else:
                return
        for curr_spot in list(remaining_spots):
            remaining_spots.remove(curr_spot)
            possible_placements = [
                (curr_spot[0],curr_spot[1],curr_spot[0]+1,curr_spot[1]),
                (curr_spot[0],curr_spot[1],curr_spot[0],curr_spot[1]+1),
                (curr_spot[0],curr_spot[1],curr_spot[0]-1,curr_spot[1]),
                (curr_spot[0],curr_spot[1],curr_spot[0],curr_spot[1]-1),
            ]
            for (r0,c0,r1,c1) in possible_placements:
                if (r1,c1) not in remaining_spots:
                    continue
                remaining_spots.remove((r1,c1))
                curr_placements.append((r0,c0,r1,c1))
                result = helper(domino_idx+1, curr_placements, remaining_spots)
                if result is not None:
                    return result
                remaining_spots.add((r1,c1))
                curr_placements.pop()
            remaining_spots.add(curr_spot)
            
    all_spots = {spot for region in puzzle['regions'] for spot in region['indices']}
    # print(all_spots)
    answer = helper(0, [], all_spots)
    assert answer is not None
    return answer