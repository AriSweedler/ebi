#!/usr/bin/env python3
import argparse
import logging
import sys

from lib.logging import setup_logging
from lib.sudoku import Sudoku


def main():
    setup_logging()
    args = parse_args()
    with open(args.sudoku_file) as f:
        sudoku = Sudoku(f)
        we_are_done = False
        while not we_are_done:
            we_are_done = sudoku.proceed()
            print(sudoku)


def parse_args():
    parser = argparse.ArgumentParser(description="Solve a sudoku from a *.sudoku file")
    parser.add_argument(
        "--sudoku_file", type=str, help="The file to pull the sudoku puzzle from"
    )
    args = parser.parse_args()
    logging.debug(f"[INIT] Parsed args | {args=}")
    return args


if __name__ == "__main__":
    main()
