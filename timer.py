import statistics
import timeit
from implementations import implementations
from load_puzzles import all_puzzles

def run_all_puzzles(puzzles,solver):
    for puzzle in puzzles:
        solver(puzzle)

if __name__ == '__main__':
    for implementation in implementations:
        TIMEIT_NUMBER = 1000
        all_times = timeit.repeat(
            lambda: run_all_puzzles(all_puzzles,implementation),
            number=TIMEIT_NUMBER,
            repeat=10
        )
        median_time = statistics.median(all_times) / TIMEIT_NUMBER
        print(median_time)