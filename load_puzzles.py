
import json


with open('all_puzzles.json','r',encoding='utf8') as f:
    all_puzzles = []
    for puzzle_data in json.load(f):
        for difficulty in ['easy','medium','hard']:
            regions = puzzle_data[f'{difficulty}_puzzle']['regions']
            for region in regions:
                region['indices'] = [tuple(spot) for spot in region['indices']]
            dominoes = puzzle_data[f'{difficulty}_puzzle']['dominoes']
            dominoes = [tuple(domino) for domino in dominoes]
            all_puzzles.append({'regions':regions,'dominoes':dominoes})