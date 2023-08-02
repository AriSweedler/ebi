#!/usr/bin/env python3
import sys
from lib.logging import setup_logging
from lib.sudoku import Sudoku


def main():
    print("Start")
    sudoku = Sudoku(sys.stdin)
    print("Parsed")
    print(f"Sudoku:\n{sudoku}")
    while True:
        sudoku.handle_box_number()
    print("Finished")


if __name__ == "__main__":
    setup_logging()
    main()
