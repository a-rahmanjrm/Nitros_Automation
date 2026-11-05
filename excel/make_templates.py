"""Generate the blank Excel templates used by Nitros Automation.

Run once:  python make_templates.py           (Locators.xlsx + Cases.xlsx)
           python make_templates.py --cases   (blank Cases.xlsx only)
Outputs go to this folder.
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation

HERE = os.path.dirname(os.path.abspath(__file__))

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)

STRATEGIES = ["XPATH", "ID", "CSS_SELECTOR", "NAME", "CLASS_NAME", "TAG_NAME"]
MATCHES = ["contains", "starts-with", "exact"]


def style_header(ws, headers, widths):
    ws.append(headers)
    for col, (title, width) in enumerate(zip(headers, widths), start=1):
        cell = ws.cell(row=1, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = HEADER_ALIGN
        ws.column_dimensions[cell.column_letter].width = width
    ws.freeze_panes = "A2"


def build_locators():
    wb = Workbook()
    ws = wb.active
    ws.title = "Locators"
    headers = ["Name", "Strategy", "Match", "Attribute", "Value", "Full XPath", "Notes"]
    style_header(ws, headers, [30, 14, 14, 14, 60, 80, 40])

    # Seed rows: the element names used by the current scripts. Value holds the
    # template fragment; paste the full XPath the script should use in column F.
    seeds = [
        ("DialerLoginUser", "ID", "exact", "id", "wweLoginUserNameField", "", "Dialer login"),
        ("DialerLoginPass", "ID", "exact", "id", "wweLoginPasswordField", "", "Dialer login"),
        ("DialerPlaceID", "ID", "exact", "id", "wweLoginPlaceInput", "", "Dialer login"),
        ("DialerLoginError", "XPATH", "exact", "id", "wweLoginErrorText", "", ""),
        ("GlobalSearchBox", "ID", "exact", "id", "GlobalSearchBox", "", "CRM search"),
        ("FirstSearchResult", "XPATH", "starts-with", "id", "id-globalSearchFlyout-1", "", "Search result in flyout"),
        ("NavigateBack", "XPATH", "exact", "id", "navigateBackButtontab-id-0", "", ""),
        ("EditCaseButton", "XPATH", "contains", "id", "lvdcg.incident.TimeTrackingCheckOut.Command.", "", "Case edit"),
        ("SaveCaseButton", "XPATH", "contains", "id", "lvdcg.incident.TimeTrackingCheckIn.Command.", "", "Case save"),
        ("CaseChannelHeader", "XPATH", "contains", "id", "headerControlsList", "", "Header, e-Ticketing check"),
        ("CaseStatusHeader", "XPATH", "contains", "id", "headerControlsList", "", "Header, Solution Provided check"),
        ("CustomerNameAnchor", "XPATH", "contains", "id", "sec_tab_contact-associatedEntityRecordName", "", ""),
        ("AddMenuButton", "XPATH", "starts-with", "id", "id-915f6055-2e07-4276-ae08-2b96c8d02c57", "", "Activity + menu"),
        ("FlyoutMenuItemSMS", "XPATH", "contains", "id", "notescontrol-createNewRecord_flyoutMenuItem_lvidg_sms", "", "Flyout SMS item"),
        ("FlyoutMenuItemEmail", "XPATH", "contains", "id", "notescontrol-createNewRecord_flyoutMenuItem_email", "", "Flyout email item"),
        ("FlyoutMenuItemNotes", "XPATH", "contains", "id", "notescontrol-createNewRecord_flyoutMenuItem_notes", "", "Flyout note item"),
        ("SMSTextInput", "XPATH", "contains", "id", "subject.fieldControl-text-input-component", "", ""),
        ("SMSSaveClose", "XPATH", "starts-with", "id", "lvidg_sms|NoRelationship|Form|Mscrm.SaveAndClosePrimary", "", ""),
        ("NoteEditor", "XPATH", "contains", "id", "rtev", "", "Note rich-text editor"),
        ("NoteAddAndClose", "XPATH", "exact", "text", "Add note and close", "", "Button label"),
        ("DiscardChangesButton", "XPATH", "starts-with", "id", "cancelButton_", "", "Dialog: Discard changes"),
        ("SaveAndContinueButton", "XPATH", "starts-with", "id", "confirmButton_", "", "Dialog: Save and continue"),
        ("ConfirmOkButton", "XPATH", "starts-with", "id", "confirmButton_", "", "Dialog: OK"),
        ("ProcessBreadCrumb", "XPATH", "contains", "id", "MscrmControls.Containers.ProcessBreadCrumb", "", "Stage indicator"),
        ("FlyoutCaseStatus", "XPATH", "contains", "id", "header_process_lvidg_casestatuscode", "", "Classification flyout"),
        ("FlyoutCaseReason", "XPATH", "contains", "id", "header_process_casetypecode", "", "Classification flyout"),
        ("FlyoutContactReason", "XPATH", "contains", "id", "header_process_lvidg_callreasoncode", "", "Classification flyout"),
        ("FlyoutTechSavvy", "XPATH", "contains", "id", "header_process_lvidg_techsavvy", "", "Classification flyout"),
        ("FlyoutPDUsage", "XPATH", "contains", "id", "header_process_lvidg_isusedlenovopdtree", "", "Classification flyout"),
        ("FlyoutPDTreeReason", "XPATH", "contains", "id", "header_process_lvidg_pdtreereasoncode", "", "Classification flyout"),
        ("FlyoutCloseButton", "XPATH", "contains", "id", "MscrmControls.Containers.ProcessStageControl-stageContentClose", "", ""),
        ("OptionServiceCall", "XPATH", "exact", "text", "Service Call", "", "Fluent option"),
        ("OptionHardwareRepair", "XPATH", "exact", "text", "Hardware Repair", "", "Fluent option"),
        ("OptionUndetermined", "XPATH", "exact", "text", "Undetermined", "", "Fluent option"),
        ("OptionNo", "XPATH", "exact", "text", "No", "", "Fluent option"),
        ("OptionETicketing", "XPATH", "exact", "text", "e-Ticketing", "", "Fluent option"),
        ("OptionEscalationComplaint", "XPATH", "exact", "text", "Escalation/Complaint", "", "Fluent option"),
        ("OptionFollowUpComplaint", "XPATH", "exact", "text", "Follow up - Complaint", "", "Fluent option"),
        ("OptionCareCall", "XPATH", "exact", "text", "Care Call", "", "Fluent option"),
        ("EmailClearFromButton", "XPATH", "contains", "id", "from.fieldControl-LookupResultsDropdown_from", "", "Email From field"),
        ("EmailFromInput", "XPATH", "contains", "id", "textInputBox_with_filter_new", "", "Email From field"),
        ("EmailBodyInput", "XPATH", "starts-with", "id", "rtev", "", "Email body"),
        ("EmailSendButton", "XPATH", "starts-with", "id", "email|NoRelationship|Form|Mscrm.Form.email.Send", "", ""),
        ("ContactCardLink", "XPATH", "contains", "id", "sec_tab_contact-associatedEntityRecordName", "", "DND flow"),
        ("ContactEditButton", "XPATH", "contains", "id", "contact|NoRelationship|Form|lvidg.contact.TimeTrackingCheckOut.Command", "", "DND flow"),
        ("ContactDetailsTab", "XPATH", "contains", "id", "tab4", "", "DND flow, title=Details"),
        ("ContactDNDToggle", "XPATH", "contains", "id", "lvidg_hasdonotdisturbf9a8a302", "", "DND flow"),
        ("ContactSaveButton", "XPATH", "contains", "id", "contact|NoRelationship|Form|lvidg.contact.TimeTrackingCheckIn.Command", "", "DND flow"),
        ("DialerMarkDone", "XPATH", "contains", "class", "wwe-sprite-mark-done", "", "Dialer"),
        ("DialerField", "ID", "exact", "id", "wweTeamCommunicatorDialerField", "", "Dialer number input"),
        ("HangupButton", "XPATH", "contains", "id", "wweVoice8HangupButton", "", "Dialer"),
        ("MobilePhoneInput", "XPATH", "exact", "aria-label", "Mobile Phone", "", "CRM contact field"),
    ]
    for row in seeds:
        ws.append([*row[:5], "", row[6]])

    # Empty rows for the locators you will add later (pre-formatted via validation).
    for _ in range(20):
        ws.append([None] * 7)

    last = ws.max_row
    dv_strategy = DataValidation(type="list", formula1='"' + ",".join(STRATEGIES) + '"', allow_blank=True)
    dv_match = DataValidation(type="list", formula1='"' + ",".join(MATCHES) + '"', allow_blank=True)
    ws.add_data_validation(dv_strategy)
    ws.add_data_validation(dv_match)
    dv_strategy.add(f"B2:B{last}")
    dv_match.add(f"C2:C{last}")

    for row in ws.iter_rows(min_row=2, max_row=last):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    readme = wb.create_sheet("README")
    readme["A1"] = "How to fill this sheet"
    readme["A1"].font = Font(bold=True, size=13)
    lines = [
        "Name: the key the code uses, e.g. GlobalSearchBox. Must be unique and have no spaces.",
        "Strategy: Selenium locator type (XPATH, ID, CSS_SELECTOR, ...).",
        "Match: contains / starts-with / exact. Used when Value is a fragment of a dynamic id.",
        "Attribute: the attribute the Value applies to (id, text, class, aria-label, ...).",
        "Value: the fragment or exact value taken from the element.",
        "Full XPath: paste the full XPath from DevTools. The script tests each match type and records the result.",
        "Notes: free text.",
    ]
    for i, text in enumerate(lines, start=3):
        readme[f"A{i}"] = text
    readme.column_dimensions["A"].width = 110

    wb.save(os.path.join(HERE, "Locators.xlsx"))


def build_cases():
    wb = Workbook()
    ws = wb.active
    ws.title = "Cases"
    style_header(ws, ["Case Number", "Notes"], [20, 70])
    for _ in range(200):
        ws.append([None, None])
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.number_format = "@"  # keep case numbers as text (leading zeros safe)
    wb.save(os.path.join(HERE, "Cases.xlsx"))


if __name__ == "__main__":
    import sys
    if "--cases" in sys.argv:
        # Only a blank Cases.xlsx; leaves your Locators.xlsx untouched.
        build_cases()
        print("Created Cases.xlsx in", HERE)
    else:
        build_locators()
        build_cases()
        print("Created Locators.xlsx and Cases.xlsx in", HERE)
