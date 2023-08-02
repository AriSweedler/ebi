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
            row_str = line.strip().split(",")
            row = self.validate_row(row_str)
            self.box_numbers.append(row)
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
        except ValueError:
            raise Exception(
                f"[SUDOKU] - Failed to convert value to number between 1 and 9 inclusive - {string=} {row_str=}"
            )

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
