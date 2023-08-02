#!/usr/bin/env python3
import sys
from lib.sudoku import Sudoku


def main():
    print("Start")
    sudoku = Sudoku(sys.stdin)
    print("Parsed")
    print(f"Sudoku:\n{sudoku}")
    print(sudoku.compact_pencilmarks([1, 2, 3, 6, 7, 8, 9]))
    print(sudoku.compact_pencilmarks([1, 3, 4, 5, 7, 9]))
    print(sudoku.compact_pencilmarks([1, 3, 4, 5, 7, 8, 9]))
    print(sudoku.compact_pencilmarks([1, 2, 3, 4, 5, 6, 8, 9]))
    print("Finished")


if __name__ == "__main__":
    main()
