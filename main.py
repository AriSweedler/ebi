#!/usr/bin/env python3
import sys
from lib.sudoku import Sudoku


def main():
    print("Start")
    sudoku = Sudoku(sys.stdin)
    print("Parsed")
    print(f"Sudoku:\n{sudoku}")
    while True:
        sudoku.handle_box_number()
        print(f"Sudoku:\n{sudoku}")
    print("Finished")


if __name__ == "__main__":
    main()
