"""Builds the Excel export: one sheet per day of the week, with each practice
laid out like the app's lanes view (Lane 1-8 as columns, swimmers listed
under their lane, plus a column for assigned swimmers not in a lane yet).
"""

from collections.abc import Iterable
from datetime import time
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from app.models import Assignment, Day, Practice, Swimmer
from app.schemas import LANE_COUNT

COLUMN_HEADERS = [f"Lane {lane}" for lane in range(1, LANE_COUNT + 1)] + ["Not in a lane"]
COLUMN_COUNT = len(COLUMN_HEADERS)

# UIndy crimson, matching the app
CRIMSON = "B20A38"
HEADER_GRAY = "E6E6EA"

THIN = Side(style="thin", color="A0A0A8")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTERED = Alignment(horizontal="center", vertical="center", wrap_text=True)


def format_time(t: time) -> str:
    """time(13, 30) -> '1:30 PM'"""
    hour = t.hour % 12 or 12
    period = "AM" if t.hour < 12 else "PM"
    return f"{hour}:{t.minute:02d} {period}"


def practice_columns(practice: Practice, swimmers: dict[int, Swimmer],
                     assignments: Iterable[Assignment],
                     lanes: dict[Assignment, int]) -> list[list[str]]:
    """Swimmer names for each column: lanes 1-8, then assigned swimmers with no lane.

    Names are sorted by last name within each column, so a printed sheet is
    easy to scan.
    """
    columns: list[list[str]] = [[] for _ in range(COLUMN_COUNT)]

    assigned = [swimmers[a.swimmer_id] for a in assignments if a.practice_id == practice.practice_id]
    assigned.sort(key=lambda s: (s.last_name.lower(), s.first_name.lower()))

    for swimmer in assigned:
        lane = lanes.get(Assignment(swimmer_id=swimmer.swimmer_id, practice_id=practice.practice_id))
        index = COLUMN_COUNT - 1 if lane is None else lane - 1   # last column = not in a lane
        columns[index].append(f"{swimmer.first_name} {swimmer.last_name}")

    return columns


def write_practice(sheet: Worksheet, row: int, practice: Practice,
                   columns: list[list[str]]) -> int:
    """Write one practice block starting at `row`. Returns the first row after it."""
    swimmer_count = sum(len(column) for column in columns)
    title = (f"{practice.practice_title}  ·  {format_time(practice.start_time)} - "
             f"{format_time(practice.end_time)}  ·  {swimmer_count} "
             f"{'swimmer' if swimmer_count == 1 else 'swimmers'}")

    # Title bar across all the columns, crimson like a selected practice in the app
    sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=COLUMN_COUNT)
    title_cell = sheet.cell(row=row, column=1, value=title)
    title_cell.font = Font(bold=True, color="FFFFFF", size=12)
    title_cell.fill = PatternFill("solid", fgColor=CRIMSON)
    title_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    sheet.row_dimensions[row].height = 22
    row += 1

    # Lane headers
    for column, header in enumerate(COLUMN_HEADERS, start=1):
        cell = sheet.cell(row=row, column=column, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor=HEADER_GRAY)
        cell.alignment = CENTERED
        cell.border = BOX
    row += 1

    # Swimmer names down each lane. Every lane gets the same number of rows
    # (at least one), so the block is a neat grid even when lanes are empty.
    height = max(1, max(len(column) for column in columns))
    for offset in range(height):
        for column, names in enumerate(columns, start=1):
            name = names[offset] if offset < len(names) else None
            cell = sheet.cell(row=row + offset, column=column, value=name)
            cell.alignment = CENTERED
            cell.border = BOX
    return row + height


def build_week_workbook(practices: Iterable[Practice], swimmers: dict[int, Swimmer],
                        assignments: Iterable[Assignment],
                        lanes: dict[Assignment, int],
                        open_on: Day = Day.MONDAY) -> bytes:
    """The whole week as an .xlsx file: a sheet for each day, Monday to Sunday.

    `open_on` is the day whose sheet is showing when the file is opened.
    """
    practices = list(practices)
    assignments = list(assignments)

    workbook = Workbook()
    workbook.remove(workbook.active)   # start empty; a sheet is added for each day below

    for day in Day:
        day_name = day.name.title()     # MONDAY -> "Monday"
        sheet = workbook.create_sheet(title=day_name)

        for column in range(1, COLUMN_COUNT + 1):
            sheet.column_dimensions[get_column_letter(column)].width = 16
        sheet.column_dimensions[get_column_letter(COLUMN_COUNT)].width = 18

        # Printing: landscape, and shrink to one page wide so no lane gets cut off
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0   # 0 = as many pages tall as it needs
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.print_options.horizontalCentered = True

        heading = sheet.cell(row=1, column=1, value=f"{day_name} practices")
        heading.font = Font(bold=True, size=16)

        day_practices = sorted((p for p in practices if p.day == day), key=lambda p: p.start_time)
        if not day_practices:
            sheet.cell(row=3, column=1, value="No practices")
            continue

        row = 3
        for practice in day_practices:
            columns = practice_columns(practice, swimmers, assignments, lanes)
            row = write_practice(sheet, row, practice, columns) + 1   # blank row between practices

    # Sheets are in Day order, so Monday (1) is sheet 0. Excel also expects the
    # sheet it opens on to be marked as the selected tab.
    workbook.active = open_on.value - 1
    workbook.active.sheet_view.tabSelected = True

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
