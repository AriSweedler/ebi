import logging
import sys
import time
from itertools import product
from typing import List

""" Ingest a '*.sudoku' file and load it into a 'Sudoku' object """

Pencilmark = List[int]


# The algorithm is simple:
# * Pencilmark everything
# * For each number that we discover (either because it was given to us or
#   because we figured it out, it's all the same):
#   * Use it to update all pencilmarks
# * If updating a pencilmark yields a new clue:
#   * Create a new box_number
#     * Only 1 number for a given cell
#     * Only 1 cell for a number in a given box/row/col
#   * Remove some pencilmarks
#     * There is a 'lock' in a line
#     * There is a 'lock' in a box
class Sudoku:
    pencilmarks = None
    box_numbers = None
    answers = [[None for _ in range(9)] for _ in range(9)]

    def __init__(self, _data):
        # Make a 9 by 9 grid, each of which contains a pencilmarked_cell
        self.pencilmarks = [
            [self.full_pencilmarked_cell() for _ in range(1, 10)] for i in range(1, 10)
        ]

        # Load all the original numbers into the 'box_numbers' queue for later processing
        self.box_numbers = list()
        for line in _data:
            row_str = [l for l in line.strip().split(",") if l != ""]
            row = self.validate_row(row_str)
            self.box_numbers.append([r for r in row])
        self.validate_input()

    def validate_input(self):
        if len(self.box_numbers) != 9:
            raise Exception("[SUDOKU] - We need 9 rows to make a valid sudoku")

    def validate_row(self, row_str):
        if len(row_str) != 9:
            raise Exception(
                f"[SUDOKU] - We need 9 columns per rows to make a valid sudoku - {row_str=}"
            )
        try:
            for string in row_str:
                num = int(string)
                if num == 0:
                    # This cell is blank
                    continue
                if not 1 <= num <= 9:
                    raise Exception(
                        f"[SUDOKU] - We need a number between 1 and 9 - {num=} {row_str=}"
                    )
        except ValueError:
            raise Exception(
                f"[SUDOKU] - Failed to convert value to number between 1 and 9 inclusive - {string=} {row_str=}"
            )
        return [int(string) for string in row_str]

    def full_pencilmarked_cell(self) -> List[int]:
        return [i for i in range(1, 10)]

    def compact_pencilmarks(self, pmarks) -> str:
        range_all = list()
        range_one = list()
        prev_num = -1
        pmarks.sort()
        for num in pmarks:
            if num > prev_num + 1:
                range_all.append([x for x in range_one])
                range_one = list()
            range_one.append(num)
            prev_num = num
        range_all.append([x for x in range_one])
        ans = ",".join(
            [
                f"{min(x)}-{max(x)}" if min(x) != max(x) else f"{min(x)}"
                for x in range_all
                if len(x) > 0
            ]
        )
        return f"{ans:10}"

    def __str__(self):
        if self.pencilmarks is None:
            return "Not initialized"

        return "\n".join(
            [
                "|".join([self.compact_pencilmarks(cell) for cell in row])
                for row in self.pencilmarks
            ]
        )

    def pop_box_number(self):
        time.sleep(0.01)
        row_i = None
        col_i = None
        value = None
        for row_i in range(len(self.box_numbers)):
            for col_i in range(len(self.box_numbers[row_i])):
                value = self.box_numbers[row_i][col_i]
                if value is not None and value != 0:
                    self.box_numbers[row_i][col_i] = None
                    self.answers[row_i][col_i] = value
                    return row_i, col_i, value
        return None, None, None

    def handle_box_number(self):
        # Find the next box number
        row_i, col_i, value = self.pop_box_number()
        if value is None:
            logging.error("Oh no - we are all out of shit")
            logging.error("\n" + str(self))
            sys.exit(1)
        logging.debug(f"We got a box number to deal with | {row_i=} {col_i=} {value=}")

        # Pop it off and process it
        self.update_pencilmarks_row(value, row_i)
        self.update_pencilmarks_col(value, col_i)
        self.update_pencilmarks_box(value, (row_i, col_i))
        self.update_pencilmarks_cell((row_i, col_i))

        logging.info(f"We have updated pencilmarks for | {row_i=} {col_i=} {value=}")
        logging.debug(self)

        # Place answers
        self.scan_answers_rows()
        self.scan_answers_cols()
        self.scan_answers_boxes()
        self.scan_answers_cells()

    def erase_pencilmark(self, value, cell_i):
        row_i, col_i = cell_i
        self.pencilmarks[row_i][col_i] = [
            x for x in self.pencilmarks[row_i][col_i] if x != value
        ]

    def update_pencilmarks_row(self, value, row_i):
        for col_i in range(9):
            self.erase_pencilmark(value, (row_i, col_i))

    def update_pencilmarks_col(self, value, col_i):
        for row_i in range(9):
            self.erase_pencilmark(value, (row_i, col_i))

    # Given an index, return the start and end of the box index
    def box_unclamp(self, index):
        remainder = index % 3
        return index - remainder, index + (3 - remainder)

    def update_pencilmarks_box(self, value, box_i):
        row_i, col_i = box_i
        box_bot, box_top = self.box_unclamp(row_i)
        box_left, box_right = self.box_unclamp(col_i)
        for row_i in range(box_bot, box_top):
            for col_i in range(box_left, box_right):
                self.erase_pencilmark(value, (row_i, col_i))

    def update_pencilmarks_cell(self, box_i):
        for value in range(1, 10):
            self.erase_pencilmark(value, box_i)

    def scan_answers_rows(self):
        for row_i in range(9):
            pencilmark_row = list(self.get_row(row_i))
            value, index = self.scan_answers(pencilmark_row)
            if value is None or index is None:
                logging.debug(
                    f"At this time, there is nothing to be found in this row | {row_i=}"
                )
                continue
            cell_i = row_i, index
            self.pen_in_number(value, cell_i)

    def scan_answers_cols(self):
        for col_i in range(9):
            pencilmark_col = list(self.get_col(col_i))
            value, index = self.scan_answers(pencilmark_col)
            if value is None or index is None:
                logging.debug(
                    f"At this time, there is nothing to be found in this col | {col_i=}"
                )
                continue
            cell_i = index, col_i
            self.pen_in_number(value, cell_i)

    def scan_answers_boxes(self):
        for box_i in product([0, 3, 6], [0, 3, 6]):
            pencilmark_box = list(self.get_box(box_i))
            value, index = self.scan_answers(pencilmark_box)
            if value is None or index is None:
                logging.debug(
                    f"At this time, there is nothing to be found in this box. | {box_i=}"
                )
                continue
            row_start, col_start = box_i
            row_i = row_start + int(index / 3)
            col_i = col_start + index % 3
            cell_i = row_i, col_i
            self.pen_in_number(value, cell_i)

    def scan_answers_cells(self):
        for row_i in range(len(self.pencilmarks)):
            for col_i in range(len(self.pencilmarks[row_i])):
                pencilmark = self.pencilmarks[row_i][col_i]
                if len(pencilmark) != 1:
                    continue
                cell_i = (row_i, col_i)
                value = pencilmark[0]
                self.pen_in_number(value, cell_i)

    def pen_in_number(self, value, cell_i):
        row_i, col_i = cell_i
        logging.info(
            f"Adding a value to the box number queue | {row_i=} {col_i=} {value=}"
        )
        if self.answers[row_i][col_i] != 0:
            logging.error(
                f"Oh dear, you're trying to place a number in a col where it already has been. | {row_i=} {col_i=} {value=}"
            )
            return
        self.box_numbers[row_i][col_i] = value

    def scan_answers(self, pencilmark_range: List[Pencilmark]):
        # Check if there are any numbers that only show up once
        counts = [0] * 10
        for pencilmark in pencilmark_range:
            for num in pencilmark:
                counts[num] += 1
        for count_i in range(len(counts)):
            if counts[count_i] != 1:
                continue
            num = count_i
            return num, count_i
        # logging.debug(f"There is nothing in this range that will give us an answer")
        return None, None

    def get_row(self, row_i):
        for col_i in range(9):
            yield self.pencilmarks[row_i][col_i]

    def get_col(self, col_i):
        for row_i in range(9):
            yield self.pencilmarks[row_i][col_i]

    def get_box(self, box_i):
        row_i, col_i = box_i
        box_bot, box_top = self.box_unclamp(row_i)
        box_left, box_right = self.box_unclamp(col_i)
        for row_i in range(box_bot, box_top):
            for col_i in range(box_left, box_right):
                yield self.pencilmarks[row_i][col_i]
