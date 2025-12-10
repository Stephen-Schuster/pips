import functools

# I sped this function up a lot with bitwise operations
@functools.cache
def solve_propagation(possibilities_tup):
    possibilities_dict = {slot: set(items) for slot, items in enumerate(possibilities_tup)}
    all_items = sorted(list(set().union(*possibilities_dict.values())))
    item_to_bit = {item: (1 << i) for i, item in enumerate(all_items)}
    bit_to_item = {v: k for k, v in item_to_bit.items()}
    
    slots = sorted(possibilities_dict.keys())
    n = len(slots)
    
    state = [0] * n
    for i, s in enumerate(slots):
        mask = 0
        for item in possibilities_dict[s]:
            mask |= item_to_bit[item]
        state[i] = mask

    changed = True
    while changed:
        changed = False
        
        for i in range(n):
            mask = state[i]
            if mask != 0 and (mask & (mask - 1)) == 0:
                locked_bit = mask
                for j in range(n):
                    if i != j and (state[j] & locked_bit):
                        state[j] &= ~locked_bit
                        changed = True

        col_counts = {}
        col_locs = {}
        
        for i in range(n):
            temp = state[i]
            while temp:
                bit = temp & -temp
                col_counts[bit] = col_counts.get(bit, 0) + 1
                col_locs[bit] = i
                temp ^= bit
        
        for bit, count in col_counts.items():
            if count == 1:
                idx = col_locs[bit]
                if state[idx] != bit:
                    state[idx] = bit
                    changed = True

        for i in range(n):
            mask_i = state[i]
            if bin(mask_i).count('1') == 2:
                for j in range(i + 1, n):
                    if state[j] == mask_i:
                        pair_mask = mask_i
                        
                        for k in range(n):
                            if k != i and k != j:
                                if (state[k] & pair_mask):
                                    state[k] &= ~pair_mask
                                    changed = True

    reduced_possibilities = {}
    for i, s in enumerate(slots):
        mask = state[i]
        valid_items = set()
        bit = 1
        while bit <= mask:
            if mask & bit:
                valid_items.add(bit_to_item.get(bit, "Unknown"))
            bit <<= 1
        reduced_possibilities[s] = valid_items
        
    return reduced_possibilities
