#!/usr/bin/env python3
import sys
from lib.logging import setup_logging
from lib.sudoku import Sudoku


def main():
    sudoku = Sudoku(sys.stdin)
    while True:
        sudoku.proceed()


if __name__ == "__main__":
    setup_logging()
    main()
