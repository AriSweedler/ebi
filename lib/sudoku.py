import os
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

        # Now go through all the original box numbers and update the
        # pencilmarks. Find the next box number. Pop it off and process it
        logging.info(
            "[INIT] Going through all the original box numbers and updating pencilmarks"
        )
        while True:
            *cell_i, value = self.pop_box_number()
            if value is None:
                break
            self.update_pencilmarks(value, cell_i)
            self.answers[cell_i[0]][cell_i[1]] = value
        logging.info("[INIT] complete")

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
        if ans == "":
            blank = "___"
            return f"{blank:14}"
        return f"{ans:14}"

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
        if os.getenv("VISUAL"):
            time.sleep(0.01)
        row_i = None
        col_i = None
        value = None
        for row_i in range(len(self.box_numbers)):
            for col_i in range(len(self.box_numbers[row_i])):
                value = self.box_numbers[row_i][col_i]
                # None means we have checked the number in this box already
                # 0 means this box is blank
                # 1-9 means this box has an answer and it is pending
                if value is not None and value != 0:
                    self.box_numbers[row_i][col_i] = None
                    self.answers[row_i][col_i] = value
                    return row_i, col_i, value
        return None, None, None

    def proceed(self):
        # Given pencilmarks, discover new answers to add
        self.scan_answers()

        # Now that we've updated everything and added new box numbers, find the
        # next unprocessed box number and update pencilmarks with it
        *cell_i, value = self.pop_box_number()
        if value is None:
            self.endgame()
        logging.debug(f"[PENCILMARKS] We have a box number to deal with | {cell_i=} {value=}")
        self.update_pencilmarks(value, cell_i)

    # Given an index, return the start and end of the box index
    def box_unclamp(self, index):
        remainder = index % 3
        return index - remainder, index + (3 - remainder)

    def erase_pencilmark(self, value, cell_i):
        row_i, col_i = cell_i
        self.pencilmarks[row_i][col_i] = [
            x for x in self.pencilmarks[row_i][col_i] if x != value
        ]

    def update_pencilmarks(self, value, cell_i):
        row_i, col_i = cell_i

        self.update_pencilmarks_row(value, row_i)
        self.update_pencilmarks_col(value, col_i)
        self.update_pencilmarks_box(value, (row_i, col_i))
        self.update_pencilmarks_cell((row_i, col_i))

        logging.debug(f"[PENCILMARKS] We have updated pencilmarks thanks to | {value=} {cell_i=}")
        logging.debug("[PENCILMARKS] [DATA]:\n" + str(self))

    def update_pencilmarks_row(self, value, row_i):
        for col_i in range(9):
            self.erase_pencilmark(value, (row_i, col_i))

    def update_pencilmarks_col(self, value, col_i):
        for row_i in range(9):
            self.erase_pencilmark(value, (row_i, col_i))

    def update_pencilmarks_box(self, value, box_i):
        row_i, col_i = box_i
        box_bot, box_top = self.box_unclamp(row_i)
        box_left, box_right = self.box_unclamp(col_i)
        for row_i in range(box_bot, box_top):
            for col_i in range(box_left, box_right):
                self.erase_pencilmark(value, (row_i, col_i))

    def update_pencilmarks_cell(self, box_i):
        row_i, col_i = box_i
        self.pencilmarks[row_i][col_i] = list()

    def scan_answers(self):
        self.is_solved() or \
        self.scan_answers_rows() or \
        self.scan_answers_cols() or \
        self.scan_answers_boxes() or \
        self.scan_answers_cells()

    def scan_answers_range(self, pencilmark_range: List[Pencilmark]):
        # Check if there are any numbers that only show up once
        found_one = [False] * 10
        for range_index in range(len(pencilmark_range)):
            pencilmark = pencilmark_range[range_index]
            for num in pencilmark:
                x = found_one[num]
                if x is False:
                    found_one[num] = range_index
                if type(x) is int:
                    found_one[num] = None
                if x is None:
                    continue
        for i in range(len(found_one)):
            if not found_one[i]:
                continue
            num = i
            index = found_one[i]
            return num, index
        # logging.debug(f"There is nothing in this range that will give us an answer")
        return None, None

    def scan_answers_rows(self):
        for row_i in range(9):
            pencilmark_row = list(self.get_range_row(row_i))
            value, index = self.scan_answers_range(pencilmark_row)
            if value is None or index is None:
                logging.debug(
                    f"[ANSWERS] [SCAN] At this time, there is nothing to be found in this row | {row_i=}"
                )
                continue
            cell_i = row_i, index

            # Log, update state, and return success
            self.log_answer(value, cell_i, "row")
            self.pen_in_number(value, cell_i)
            return True

    def scan_answers_cols(self):
        for col_i in range(9):
            pencilmark_col = list(self.get_range_col(col_i))
            value, index = self.scan_answers_range(pencilmark_col)
            if value is None or index is None:
                logging.debug(
                    f"[ANSWERS] [SCAN] At this time, there is nothing to be found in this col | {col_i=}"
                )
                continue
            cell_i = index, col_i

            # Log, update state, and return success
            self.log_answer(value, cell_i, "col")
            self.pen_in_number(value, cell_i)
            return True

    def scan_answers_boxes(self):
        for box_i in product([0, 3, 6], [0, 3, 6]):
            pencilmark_box = list(self.get_range_box(box_i))
            value, index = self.scan_answers_range(pencilmark_box)
            if value is None or index is None:
                logging.debug(
                    f"[ANSWERS] [SCAN] At this time, there is nothing to be found in this box. | {box_i=}"
                )
                continue
            row_start, col_start = box_i
            row_i = row_start + int(index / 3)
            col_i = col_start + index % 3
            cell_i = row_i, col_i

            # Log, update state, and return success
            self.log_answer(value, cell_i, "box")
            self.pen_in_number(value, cell_i)
            return True

    def scan_answers_cells(self):
        for row_i in range(len(self.pencilmarks)):
            for col_i in range(len(self.pencilmarks[row_i])):
                pencilmark = self.pencilmarks[row_i][col_i]
                if len(pencilmark) != 1:
                    continue
                cell_i = (row_i, col_i)
                value = pencilmark[0]

                # Log, update state, and return success
                self.log_answer(value, cell_i, "cell")
                self.pen_in_number(value, cell_i)
                return True

    def log_answer(self, value, cell_i, reason):
        logging.info(
                f"[ANSWERS] [SCAN] The value can only be in one place | {reason=} {value=} {cell_i=}"
                )

    def pen_in_number(self, value, cell_i):
        row_i, col_i = cell_i
        logging.debug(
            f"[ANSWERS] [RECORD] Trying to add a value to the box_numbers queue | {value=} {cell_i=}"
        )
        self.box_numbers[row_i][col_i] = value
        if self.answers[row_i][col_i] != None:
            logging.error(
                f"[ANSWERS] [RECORD] You are placing a number in a col where it already has been. | {value=} {cell_i=}"
            )
            sys.exit(1)
            return

    def get_range_row(self, row_i):
        for col_i in range(9):
            yield self.pencilmarks[row_i][col_i]

    def get_range_col(self, col_i):
        for row_i in range(9):
            yield self.pencilmarks[row_i][col_i]

    def get_range_box(self, box_i):
        row_i, col_i = box_i
        box_bot, box_top = self.box_unclamp(row_i)
        box_left, box_right = self.box_unclamp(col_i)
        for row_i in range(box_bot, box_top):
            for col_i in range(box_left, box_right):
                yield self.pencilmarks[row_i][col_i]

    def is_solved(self):
        for row in self.answers:
            for cell in row:
                if cell is None:
                    return False
        return True

    def dump_answers(self):
        ans = list()
        for row in self.answers:
            ans.append("|".join([str(r) if r else "_" for r in row]))
        return '\n'.join(["Dumping answer:", *ans])

    def endgame(self):
        if self.is_solved():
            logging.info(f"[ENDGAME] Solved!")
            logging.info("[ENDGAME] " + self.dump_answers())
            sys.exit(0)

        logging.error("[ENDGAME] [FAIL] Oh no - we are all out of clues")
        logging.error("[ENDGAME] [FAIL] \n" + str(self))
        logging.error("[ENDGAME] [FAIL] " + self.dump_answers())
        sys.exit(1)
