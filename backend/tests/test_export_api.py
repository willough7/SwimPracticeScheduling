"""Tests for GET /export/week.xlsx (the Excel download).

The response is a real .xlsx file, so these tests open it with openpyxl and
check what's in the cells.
"""

from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app.main import app

client = TestClient(app)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
LANE_HEADERS = [f"Lane {n}" for n in range(1, 9)] + ["Not in a lane"]

def create_swimmer(first_name: str, last_name: str) -> int:
    response = client.post("/swimmers", json={"first_name": first_name, "last_name": last_name,
                                              "weights_group": "FOUR_DAY"})
    assert response.status_code == 201
    return response.json()["swimmer_id"]

def create_practice(day: int, start: str, end: str, title: str) -> int:
    response = client.post("/practices", json={"day": day, "start_time": start,
                                               "end_time": end, "practice_title": title})
    assert response.status_code == 201
    return response.json()["practice_id"]

def download_workbook():
    response = client.get("/export/week.xlsx")
    assert response.status_code == 200
    return load_workbook(BytesIO(response.content))

def sheet_rows(sheet) -> list[tuple]:
    return list(sheet.iter_rows(values_only=True))


def test_export_is_an_xlsx_download():
    response = client.get("/export/week.xlsx")

    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert 'attachment; filename="practice-schedule.xlsx"' == response.headers["content-disposition"]

def test_export_has_a_sheet_for_each_day():
    assert download_workbook().sheetnames == DAYS

def test_day_with_no_practices_says_so():
    rows = sheet_rows(download_workbook()["Tuesday"])

    assert rows[0][0] == "Tuesday practices"
    assert rows[2][0] == "No practices"

def test_practice_block_has_title_lane_headers_and_swimmers():
    practice_id = create_practice(5, "06:00:00", "07:30:00", "Morning Swim")
    mia = create_swimmer("Mia", "Hughes")
    ivy = create_swimmer("Ivy", "Baker")
    client.put(f"/practices/{practice_id}/swimmers/{mia}")
    client.put(f"/practices/{practice_id}/swimmers/{ivy}")
    client.put(f"/practices/{practice_id}/swimmers/{mia}/lane", json={"lane": 3})

    rows = sheet_rows(download_workbook()["Friday"])

    assert rows[2][0] == "Morning Swim  ·  6:00 AM - 7:30 AM  ·  2 swimmers"
    assert list(rows[3]) == LANE_HEADERS
    assert rows[4][2] == "Mia Hughes"      # lane 3 is the third column
    assert rows[4][8] == "Ivy Baker"       # assigned but not in a lane

def test_practices_are_in_start_time_order():
    create_practice(1, "14:30:00", "16:30:00", "Afternoon Swim")
    create_practice(1, "06:00:00", "07:30:00", "Morning Swim")

    titles = [row[0] for row in sheet_rows(download_workbook()["Monday"])
              if row[0] and "·" in row[0]]

    assert titles[0].startswith("Morning Swim")
    assert titles[1].startswith("Afternoon Swim")

def test_swimmers_in_a_lane_are_sorted_by_last_name():
    practice_id = create_practice(3, "06:00:00", "07:30:00", "Morning Swim")
    for first, last in [("Zoe", "Ward"), ("Ben", "Adams"), ("Mia", "Hughes")]:
        swimmer_id = create_swimmer(first, last)
        client.put(f"/practices/{practice_id}/swimmers/{swimmer_id}")
        client.put(f"/practices/{practice_id}/swimmers/{swimmer_id}/lane", json={"lane": 1})

    rows = sheet_rows(download_workbook()["Wednesday"])

    assert [rows[4][0], rows[5][0], rows[6][0]] == ["Ben Adams", "Mia Hughes", "Zoe Ward"]

def test_sheets_print_landscape_one_page_wide():
    sheet = download_workbook()["Friday"]

    assert sheet.page_setup.orientation == "landscape"
    assert sheet.page_setup.fitToWidth == 1

def test_file_opens_on_monday_by_default():
    assert download_workbook().active.title == "Monday"

def test_day_parameter_picks_the_sheet_the_file_opens_on():
    response = client.get("/export/week.xlsx", params={"day": 5})
    assert response.status_code == 200

    assert load_workbook(BytesIO(response.content)).active.title == "Friday"

def test_invalid_day_parameter_is_422_error():
    assert client.get("/export/week.xlsx", params={"day": 8}).status_code == 422
