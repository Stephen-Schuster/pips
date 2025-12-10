import statistics
import timeit

from func_timeout import FunctionTimedOut, func_timeout
from implementations import implementations
from load_puzzles import all_puzzles

def run_all_puzzles(puzzles,solver):
    for puzzle in puzzles:
        try:
            func_timeout(10, solver, args=(puzzle,))
        except FunctionTimedOut:
            continue

if __name__ == '__main__':
    for implementation in implementations:
        all_times = timeit.repeat(
            lambda: run_all_puzzles(all_puzzles,implementation),
            number=1,
            repeat=5
        )
        median_time = statistics.median(all_times)
        print(median_time)