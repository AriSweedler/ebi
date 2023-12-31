import logging
import sys
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
    initial_puzzle = None
    answers = [[None for _ in range(9)] for _ in range(9)]
    used_locks = set()
    used_daggers = set()

    def __init__(self, _data):
        # Init caches for "advanced technique"s
        self.used_locks = set()
        self.used_daggers = set()

        # Make a 9 by 9 grid, each of which contains a pencilmarked_cell
        self.pencilmarks = [
            [self.full_pencilmarked_cell() for _ in range(1, 10)] for i in range(1, 10)
        ]

        # Load all the original numbers into the 'box_numbers' queue for later processing
        self.box_numbers = list()
        self.initial_puzzle = list()
        for line in _data:
            row_str = [l for l in line.strip().split(",") if l != ""]
            row = self.validate_row(row_str)
            self.box_numbers.append([r for r in row])
            self.initial_puzzle.append([r for r in row])
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
            logging.info(f"Placing a value into the cell because it is part of the original puzzle | {value=} {cell_i=}")
            while self.update_pencilmarks(value, cell_i, no_daggers=True, no_locks=True):
                pass
            self.answers[cell_i[0]][cell_i[1]] = value
        logging.info(f"[INIT] complete")

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
                "|".join([self.compact_pencilmarks(cell) for cell in row]).strip()
                for row in self.pencilmarks
            ]
        )

    def pop_box_number(self):
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
            return True
        logging.debug(
            f"[PENCILMARKS] We have a box number to deal with | {cell_i=} {value=}"
        )
        while self.update_pencilmarks(value, cell_i):
            pass

    def erase_pencilmark(self, value, cell_i):
        row_i, col_i = cell_i
        self.pencilmarks[row_i][col_i] = [
            x for x in self.pencilmarks[row_i][col_i] if x != value
        ]

    def update_pencilmarks(self, value, cell_i, no_daggers=False, no_locks=False):
        row_i, col_i = cell_i
        original = self.hash_pencilmarks()

        self.update_pencilmarks_cell(cell_i)
        if self.hash_pencilmarks() != original:
            logging.debug(f"[PENCILMARKS] [CELL] We have updated pencilmarks because of cell | {cell_i=}")
            self.log_pencilmarks()
            return True

        self.update_pencilmarks_row(value, row_i)
        if self.hash_pencilmarks() != original:
            logging.debug(f"[PENCILMARKS] [ROW] We have updated pencilmarks because of row | {value=} {cell_i=}")
            self.log_pencilmarks()
            return True

        self.update_pencilmarks_col(value, col_i)
        if self.hash_pencilmarks() != original:
            logging.debug(f"[PENCILMARKS] [COL] We have updated pencilmarks because of col | {value=} {cell_i=}")
            self.log_pencilmarks()
            return True

        self.update_pencilmarks_box(value, cell_i)
        if self.hash_pencilmarks() != original:
            logging.debug(f"[PENCILMARKS] [BOX] We have updated pencilmarks because of box | {value=} {cell_i=}")
            self.log_pencilmarks()
            return True

        if not no_locks:
            self.update_pencilmarks_locks()
            if self.hash_pencilmarks() != original:
                logging.debug(f"[PENCILMARKS] [LOCK] We have updated pencilmarks because of a lock")
                self.log_pencilmarks()
                return True

        if not no_daggers:
            updates = self.update_pencilmarks_daggers()
            if len(updates) != 0:
                logging.debug(f"[PENCILMARKS] [DAGGER] We have updated pencilmarks because of a dagger | {updates=}")
                self.log_pencilmarks()
                return True

        return False

    def update_pencilmarks_row(self, value, row_i):
        for col_i in range(9):
            self.erase_pencilmark(value, (row_i, col_i))

    def update_pencilmarks_col(self, value, col_i):
        for row_i in range(9):
            self.erase_pencilmark(value, (row_i, col_i))

    def update_pencilmarks_box(self, value, cell_i):
        row_i, col_i = cell_i
        box_i = self.get_box_i_from_cell(cell_i)
        row_start = 3 * int(box_i / 3)
        col_start = 3 * int(box_i % 3)
        for row_i in range(row_start, row_start + 3):
            for col_i in range(col_start, col_start + 3):
                self.erase_pencilmark(value, (row_i, col_i))

    def update_pencilmarks_cell(self, cell_i):
        row_i, col_i = cell_i
        self.pencilmarks[row_i][col_i] = list()

    # This function takes us from weeny-hut jr to the salty spitoon.
    #
    # A lock is a pair of cells in a line that can only be 2 values. Any cell
    # in that line cannot have either of their values, so we can use this to
    # clear pencilmarks
    def update_pencilmarks_locks(self):
        did_work = False
        for lock in self.identify_locks():
            did_work = True
            orientation, values, cells = lock
            logging.debug(
                f"[PENCILMARKS] [LOCK] [IDENTIFY] We found a lock | {orientation=} {values=}, {cells=}"
            )

            # Destructure the answer
            row = list()
            col = list()
            for cell in cells:
                row.append(cell[0])
                col.append(cell[1])

            if orientation == "row":
                row_i = row[0]
                for col_i in [c for c in range(9) if c not in col]:
                    for value in values:
                        reason = f"lock in row {cells=} have {values}"
                        cell_i = (row_i, col_i)
                        self.log_pencilmark_lock(value, cell_i, reason)
                        self.erase_pencilmark(value, cell_i)
            elif orientation == "col":
                col_i = col[0]
                for row_i in [r for r in range(9) if r not in row]:
                    for value in values:
                        reason = f"lock in col {cells=} have {values}"
                        cell_i = (row_i, col_i)
                        self.log_pencilmark_lock(value, cell_i, reason)
                        self.erase_pencilmark(value, cell_i)
            elif orientation == "box":
                cell_in_relevant_box = (row[0], col[0])
                for cell_i in [
                    ci
                    for ci in self.get_box_range_from_cell(cell_in_relevant_box)
                    if ci not in cells
                ]:
                    for value in values:
                        reason = f"lock in box {cells=} have {values}"
                        self.log_pencilmark_lock(value, cell_i, reason)
                        self.erase_pencilmark(value, cell_i)
            else:
                logging.error(
                    f"[PENCILMARKS] [LOCK] [FAIL] Unknown orientation from 'identify_locks' | {orientation=}"
                )
                sys.exit(1)
        return did_work

    def log_pencilmark_lock(self, value, cell_i, reason):
        # logging.debug(f"[PENCILMARKS] [LOCK] [ERASE] [ATTEMPT] | {value=} {cell_i=} {reason=}")
        row_i, col_i = cell_i
        if value in self.pencilmarks[row_i][col_i]:
            logging.info(f"[PENCILMARKS] [LOCK] [ERASE] | {value=} {cell_i=} {reason=}")

    def hash_lockcell(self, lockcell):
        orientation, index, pencilmarks, _ = lockcell
        pm_hash = "_".join([str(p) for p in pencilmarks])
        hashme = tuple((orientation, pm_hash, index))
        return hash(hashme)

    def identify_locks(self):
        # Make a tree-style data structure.
        # 1st layer: index ==> row, col, box & WHICH rcb it is
        # 2nd layer: index ==> len(pencilmarks)
        # 3rd layer: index ==> hash(pencilmarks)
        # Value: cell_i
        #
        # If we ever get a collision, then we have a lock. Return it as:
        # ORIENTATION, PENCILMARKS, [CELL_I]
        #
        # An alternative way to do this is to just hash all those indexing values...
        lockbox = dict()
        for cell_i in product(range(9), range(9)):
            row_i, col_i = cell_i
            pencilmarks = self.pencilmarks[row_i][col_i]
            box_i = self.get_box_i_from_cell(cell_i)
            for lockcell in [
                ("row", row_i, pencilmarks, cell_i),
                ("col", col_i, pencilmarks, cell_i),
                ("box", box_i, pencilmarks, cell_i),
            ]:
                my_hash = self.hash_lockcell(lockcell)
                if lockbox.get(my_hash) == None:
                    lockbox[my_hash] = list()
                lockbox[my_hash].append(lockcell)

        # Check for any colissions ==> it is a lock
        for key, lockcell_list in lockbox.items():
            orientation, _, pencilmarks, cell_i = lockcell_list[0]

            # Don't use this lock if it doesn't make sense to
            if not 2 <= len(lockcell_list) <= 3:
                continue
            if len(lockcell_list) != len(pencilmarks):
                continue

            # Make sure to only use this lock once.
            if key in self.used_locks:
                continue
            self.used_locks.add(key)

            # return in the special format (different from lockcell)
            yield orientation, pencilmarks, [lockcell[3] for lockcell in lockcell_list]

    # Example:
    #
    #     _,_,_ | _,_,_ | _,_,_
    #     1,2,3 | _,_,_ | 4,5,6
    #     4,5,_ | _,_,_ | 8,9,_
    #     _____________________
    #     _,_,7 | _,_,_ | _,_,_
    #     _,_,_ | _,_,_ | _,_,_
    #     _,_,_ | _,_,_ | _,_,_
    #
    # Thanks to "dagger"s, we know where the 7 goes in the top right box
    def update_pencilmarks_daggers(self):
        # For each box, check each row/col and see if we have a dagger
        updates = list()
        for dagger in self.identify_daggers():
            orientation, value, cells = dagger
            # logging.debug(f"[PENCILMARKS] [DAGGER] [IDENTIFY] We found a dagger | {orientation=} {value=}, {cells=}")

            if orientation == "row":
                row_i, _ = cells[0]
                for col_i in [c for c in range(9)]:
                    reason = f"dagger in row {cells=}"
                    cell_i = (row_i, col_i)
                    if cell_i in cells:
                        continue
                    if self.erase_pencilmark_from_dagger(value, cell_i, reason):
                        updates.append(reason, cell_i)
                return updates
            elif orientation == "col":
                _, col_i = cells[0]
                for row_i in [r for r in range(9)]:
                    reason = f"dagger in col {cells=}"
                    cell_i = (row_i, col_i)
                    if cell_i in cells:
                        continue
                    if self.erase_pencilmark_from_dagger(value, cell_i, reason):
                        pass
            else:
                logging.error(
                    f"[PENCILMARKS] [DAGGER] [FAIL] Unknown orientation from 'identify_daggers' | {orientation=}"
                )
                sys.exit(1)

        return updates

    def dagger_cardinality(self, num, dagger_range):
        count = 0
        for cell_i in dagger_range:
            row_i, col_i = cell_i
            if num in self.pencilmarks[row_i][col_i]:
                count += 1
        if count == 1:
            # logging.debug(f"[PENCILMARKS] [DAGGER] Not a real one")
            pass
        return count

    def identify_daggers(self):
        for orientation, dagger_range, extra_range in self.generate_dagger_range():
            for num in range(1, 10):
                # Get the set of pencilmarks in a range
                if num not in self.get_pencilmark_set_in_range_cells(dagger_range):
                    continue
                if num in self.get_pencilmark_set_in_range_cells(extra_range):
                    continue

                if self.dagger_cardinality(num, dagger_range) == 1:
                    continue

                # Make sure to only use this lock once.
                key = hash(tuple((orientation, num, tuple(dagger_range))))
                if key in self.used_daggers:
                    continue
                self.used_daggers.add(key)

                # return in the special format
                yield orientation, num, dagger_range

    def generate_dagger_range(self):
        for box_i in range(9):
            r, c = list(self.get_box_range_from_box_i(box_i))[0]
            for o0, o1, o2 in [(0, 1, 2), (2, 0, 1), (1, 2, 0)]:
                yield "row", list(product([r + o0], [c, c + 1, c + 2])), list(
                    product([r + o1, r + o2], [c, c + 1, c + 2])
                )
                yield "col", list(product([r, r + 1, r + 2], [c + o0])), list(
                    product([r, r + 1, r + 2], [c + o1, c + o2])
                )

    def erase_pencilmark_from_dagger(self, value, cell_i, reason):
        # logging.debug(f"[PENCILMARKS] [DAGGER] [ERASE] [ATTEMPT] | {value=} {cell_i=} {reason=}")
        row_i, col_i = cell_i
        if value not in self.pencilmarks[row_i][col_i]:
            return False
        logging.info(
            f"[PENCILMARKS] [DAGGER] [ERASE] | {value=} {cell_i=} {reason=}"
        )
        self.pencilmarks[row_i][col_i] = [
            x for x in self.pencilmarks[row_i][col_i] if x != value
        ]

    def scan_answers(self):
        self.is_solved() or self.scan_answers_rows() or self.scan_answers_cols() or self.scan_answers_boxes() or self.scan_answers_cells()

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
            pencilmark_row = list(self.get_pencilmarks_in_range_row(row_i))
            value, index = self.scan_answers_range(pencilmark_row)
            if value is None or index is None:
                # logging.debug(f"[ANSWERS] [SCAN] At this time, there is nothing to be found in this row | {row_i=}")
                continue
            cell_i = row_i, index

            # Log, update state, and return success
            self.log_answer(value, cell_i, "row")
            self.pen_in_number(value, cell_i)
            return True

    def scan_answers_cols(self):
        for col_i in range(9):
            pencilmark_col = list(self.get_pencilmarks_in_range_col(col_i))
            value, index = self.scan_answers_range(pencilmark_col)
            if value is None or index is None:
                # logging.debug(f"[ANSWERS] [SCAN] At this time, there is nothing to be found in this col | {col_i=}")
                continue
            cell_i = index, col_i

            # Log, update state, and return success
            self.log_answer(value, cell_i, "col")
            self.pen_in_number(value, cell_i)
            return True

    def scan_answers_boxes(self):
        for cell_i in product([0, 3, 6], [0, 3, 6]):
            pencilmark_box = list(self.get_pencilmarks_in_range_box(cell_i))
            value, index = self.scan_answers_range(pencilmark_box)
            if value is None or index is None:
                # logging.debug(f"[ANSWERS] [SCAN] At this time, there is nothing to be found in this box. | {cell_i=}")
                continue
            row_start, col_start = cell_i
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
        logging.debug(
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
                f"[ANSWERS] [RECORD] [FAIL] You are placing a number in a col where it already has been. | {value=} {cell_i=}"
            )
            sys.exit(1)
            return

    def get_pencilmarks_in_range_row(self, row_i):
        for col_i in range(9):
            yield self.pencilmarks[row_i][col_i]

    def get_pencilmarks_in_range_col(self, col_i):
        for row_i in range(9):
            yield self.pencilmarks[row_i][col_i]

    def get_pencilmarks_in_range_box(self, cell_i):
        range_obj = self.get_box_range_from_cell(cell_i)
        for r, c in range_obj:
            yield self.pencilmarks[r][c]

    def get_pencilmark_set_in_range_cells(self, cells):
        ans = set()
        for cell_i in cells:
            r, c = cell_i
            for pencilmark in self.pencilmarks[r][c]:
                ans.add(pencilmark)
        return ans

    def get_box_range_from_box_i(self, box_i):
        row_start = 3 * int(box_i / 3)
        col_start = 3 * int(box_i % 3)
        for row_i in range(row_start, row_start + 3):
            for col_i in range(col_start, col_start + 3):
                yield row_i, col_i

    def get_box_range_from_cell(self, cell_i):
        box_i = self.get_box_i_from_cell(cell_i)
        for ans in self.get_box_range_from_box_i(box_i):
            yield ans

    def get_box_i_from_cell(self, cell_i):
        row_i, col_i = cell_i
        return 3 * int(row_i / 3) + int(col_i / 3)

    def is_solved(self):
        for row in self.answers:
            for cell in row:
                if cell is None:
                    return False
        return True

    def log_pencilmarks(self):
        logging.debug(f"[PENCILMARKS] [DATA]:\n" + str(self))

    def dump_answers(self):
        ans = list()
        for row in self.answers:
            ans.append("|".join([str(r).strip() if r else "_" for r in row]))
        return "\n".join(["Dumping answer:", *ans])

    def dump_initial_puzzle(self):
        ip = list()
        for row in self.initial_puzzle:
            ip.append("|".join([str(r) if r else "_" for r in row]))
        return "\n".join(["Dumping initial_puzzle:", *ip])

    def endgame(self):
        if self.is_solved():
            logging.info(f"[ENDGAME] Solved!")
            logging.info(f"[ENDGAME] " + self.dump_initial_puzzle())
            logging.info(f"[ENDGAME] " + self.dump_answers())
            return True

        logging.error(f"[ENDGAME] [FAIL] Oh no - we are all out of clues")
        logging.error(f"[ENDGAME] [FAIL] " + self.dump_initial_puzzle())
        logging.error(f"[ENDGAME] [FAIL] \n" + str(self))
        logging.error(f"[ENDGAME] [FAIL] " + self.dump_answers())
        sys.exit(1)

    def hash_pencilmarks(self):
        hashme = ""
        for r, c in product(range(9), range(9)):
            hashme += "".join([str(n) for n in self.pencilmarks[r][c]])
        return hash(hashme)

