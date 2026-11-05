"""Read Locators.xlsx and Cases.xlsx, and write match types back to Locators.xlsx."""
from openpyxl import load_workbook

LOCATORS_SHEET = "Locators"
CASES_SHEET = "Cases"


def _sheet(wb, preferred):
    return wb[preferred] if preferred in wb.sheetnames else wb.worksheets[0]


def _text(value):
    return "" if value is None else str(value).strip()


def read_locators(path):
    """Return one dict per locator row, keyed by the header names, plus '_row' (Excel row number)."""
    wb = load_workbook(path, data_only=True)
    ws = _sheet(wb, LOCATORS_SHEET)
    headers = [_text(c.value) for c in ws[1]]
    if "Name" not in headers:
        raise ValueError(f"'{path}' has no 'Name' column in its first row")
    rows = []
    for row_number, values in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        record = {h: _text(v) for h, v in zip(headers, values) if h}
        if not record.get("Name"):
            continue
        record["_row"] = row_number
        rows.append(record)
    wb.close()
    return rows


LOCATOR_FIELDS = ["Name", "Strategy", "Match", "Attribute", "Value", "Full XPath", "Notes"]


def write_locator(path, row_number, data):
    """Create (row_number=None) or update a locator row. Returns the row number used.

    Creating reuses the first empty row, so existing row numbers never move.
    """
    wb = load_workbook(path)
    ws = _sheet(wb, LOCATORS_SHEET)
    headers = [_text(c.value) for c in ws[1]]
    name_col = headers.index("Name") + 1
    if row_number is None:
        row_number = next(
            (r for r in range(2, ws.max_row + 1) if not _text(ws.cell(row=r, column=name_col).value)),
            ws.max_row + 1,
        )
    for field in LOCATOR_FIELDS:
        if field in headers:
            ws.cell(row=row_number, column=headers.index(field) + 1).value = data.get(field) or None
    wb.save(path)
    wb.close()
    return row_number


def delete_locator(path, row_number):
    """Clear a locator row. The row stays in place so other row numbers do not shift."""
    wb = load_workbook(path)
    ws = _sheet(wb, LOCATORS_SHEET)
    headers = [_text(c.value) for c in ws[1]]
    for field in LOCATOR_FIELDS:
        if field in headers:
            ws.cell(row=row_number, column=headers.index(field) + 1).value = None
    wb.save(path)
    wb.close()


def update_locator_match(path, row_number, match):
    """Save the match type that worked for a locator. Raises PermissionError if the file is open in Excel."""
    wb = load_workbook(path)
    ws = _sheet(wb, LOCATORS_SHEET)
    headers = [_text(c.value) for c in ws[1]]
    column = headers.index("Match") + 1
    ws.cell(row=row_number, column=column).value = match
    wb.save(path)
    wb.close()


def read_cases(path):
    """Return [{'case_number': ..., 'notes': ...}] for every non-empty row."""
    wb = load_workbook(path, data_only=True)
    ws = _sheet(wb, CASES_SHEET)
    headers = [_text(c.value) for c in ws[1]]
    if "Case Number" not in headers:
        raise ValueError(f"'{path}' has no 'Case Number' column in its first row")
    number_col = headers.index("Case Number")
    notes_col = headers.index("Notes") if "Notes" in headers else None
    cases = []
    for values in ws.iter_rows(min_row=2, values_only=True):
        number = _text(values[number_col])
        if not number:
            continue
        notes = _text(values[notes_col]) if notes_col is not None else ""
        cases.append({"case_number": number, "notes": notes})
    wb.close()
    return cases
