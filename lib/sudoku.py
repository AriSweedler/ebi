import time
from typing import List

""" Ingest a '*.sudoku' file and load it into a 'Sudoku' object """


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
        return ",".join(
            [
                f"{min(x)}-{max(x)}" if min(x) != max(x) else f"{min(x)}"
                for x in range_all
                if len(x) > 0
            ]
        )

        print(f"Trying co compact {pmarks=}")
        return ".".join([str(s) for s in pmarks])

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
        time.sleep(1)
        row_i = None
        col_i = None
        value = None
        for row_i in range(len(self.box_numbers)):
            for col_i in range(len(self.box_numbers[row_i])):
                value = self.box_numbers[row_i][col_i]
                if value is not None and value != 0:
                    self.box_numbers[row_i][col_i] = None
                    return row_i, col_i, value
        return None, None, None

    def handle_box_number(self):
        # Find the next box number
        row_i, col_i, value = self.pop_box_number()
        if value is None:
            print("Oh no - we are all out of shit")
            print(self)
            os.exit(1)
        print(f"We got a box number to deal with | {row_i=} {col_i=} {value=}")

        # Pop it off and process it
        self.update_pencilmarks_row(value, row_i)
        self.update_pencilmarks_col(value, col_i)
        self.update_pencilmarks_box(value, (row_i, col_i))

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
