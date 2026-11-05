# Nitros Automation: User Manual

A step-by-step guide to installing Nitros Automation, finding page elements with **Katalon Recorder**, building your own automations, and doing your **first run**.

> **Who this is for:** support and operations agents who work cases in Dynamics 365 (and optionally a Genesys WWE dialer). You don't need to know how to program. You will need to copy and paste a few commands and fill in some Excel cells.

---

## Table of Contents

1. [How Nitros Automation works](#1-how-nitros-automation-works)
2. [Install the tool (one time)](#2-install-the-tool-one-time)
3. [Find elements with Katalon Recorder](#3-find-elements-with-katalon-recorder)
4. [Tour of the web UI](#4-tour-of-the-web-ui)
5. [Your first run, step by step](#5-your-first-run-step-by-step)
6. [Build your own automation (worked example)](#6-build-your-own-automation-worked-example)
7. [Run from the command line](#7-run-from-the-command-line)
8. [Troubleshooting](#8-troubleshooting)
9. [Good practice and data safety](#9-good-practice-and-data-safety)
10. [Quick reference](#10-quick-reference)

---

## 1. How Nitros Automation works

You describe a task **once**, and the tool repeats it for every case number in an Excel sheet.

```text
 Cases.xlsx ──► for each case number ──► Case flow (list of steps)
                                            │
                       each step uses ──────┼──► a Locator  (where to click / type)   ← Locators.xlsx
                                            ├──► a Template (what to type)            ← Templates tab
                                            └──► Variables  ({case_number}, {CX_name}, …)
                                                     ▲
                                                     └── filled by Scrape steps (read text off the page)
```

### Key terms

| Term | Meaning | Where it lives |
| --- | --- | --- |
| **Locator** | A named "address" of one element on the page, for example `GlobalSearchBox` | `excel/Locators.xlsx` (edited in the **Locators** tab) |
| **Step** | One action: click, type, open a URL, read a value… | Inside a flow |
| **Flow** | An ordered list of steps with a name, for example *Search and open case* | `data/flows.json` (edited in the **Flows** tab) |
| **Setup flow** | A flow that runs **once** before the cases, for example *Dialer login* | Chosen in the **Run** tab |
| **Case flow** | A flow that runs **once per case number** | Chosen in the **Run** tab |
| **Template** | Message text with `{placeholders}` | `data/message_templates/*.txt` (the **Templates** tab) |
| **Scrape variable** | A value read from the page and saved under a name, for example `CX_name` | `data/scrape_map.json` (the **Scrape data** tab) |

---

## 2. Install the tool (one time)

### 2.1 What you need

| Software | Version | Get it from |
| --- | --- | --- |
| Python | 3.10 or newer | <https://www.python.org/downloads/>. **Tick "Add python.exe to PATH"** in the installer |
| Google Chrome | latest | <https://www.google.com/chrome/> |
| Git (optional) | any | <https://git-scm.com/>. Only needed if you clone the project instead of downloading the ZIP |
| Katalon Recorder | latest | Chrome Web Store (see [section 3](#3-find-elements-with-katalon-recorder)) |

To check Python, open **PowerShell** and run:

```powershell
python --version
```

You should see `Python 3.10.x` or higher. If you get "not recognized", reinstall Python with **Add to PATH** ticked.

### 2.2 Get the project

```powershell
git clone https://github.com/arahmanjrm/Nitros_Automation.git
cd Nitros_Automation
```

No Git? On GitHub click **Code → Download ZIP**, extract it, then in PowerShell `cd` into the extracted `Nitros_Automation` folder.

### 2.3 Create a virtual environment and install the dependencies

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

When the environment is active, your prompt starts with `(.venv)`.

> **"running scripts is disabled on this system"?** Run this once, then try `Activate.ps1` again:
>
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

> **Every new PowerShell window:** `cd` into the project folder and run `.venv\Scripts\Activate.ps1` again before using the tool.

### 2.4 Create your case sheet

```powershell
python excel/make_templates.py --cases
```

This creates `excel/Cases.xlsx` with a **Case Number** column and a **Notes** column.

> ⚠️ **Always include `--cases`.** Running `make_templates.py` *without* it also rebuilds `Locators.xlsx` from scratch, and **every locator you added or fixed is lost**.

---

## 3. Find elements with Katalon Recorder

To click or type into something, the tool must know **how to find it on the page**. That is the locator. Katalon Recorder is a free browser extension that records your clicks and shows the ID, name, CSS and XPath of every element you touch. It is the easiest way to get locator values.

### 3.1 Install Katalon Recorder

1. Open Chrome and go to the **Chrome Web Store** (<https://chromewebstore.google.com>).
2. Search for **Katalon Recorder** (published by Katalon). The extension is also available for Microsoft Edge and Firefox.
3. Click **Add to Chrome → Add extension**.
4. Click the puzzle-piece icon 🧩 in Chrome's toolbar and **pin** Katalon Recorder so its icon is always visible.

> Your company may control which extensions you can install. If the store blocks it, ask IT, or use the built-in DevTools method in [3.5](#35-alternative-chrome-devtools-no-extension).

### 3.2 Record an element

1. In Chrome, open the CRM page that has the element you need (for example the Dynamics 365 home page with the search box).
2. Click the **Katalon Recorder** icon. Its window opens.
3. Click **New** to create a test case (any name, for example `Locators`).
4. Click **Record** (the red button).
5. Go back to the CRM tab and **do the action once by hand**: click the search box, type something, click a result, and so on.
6. Go back to Katalon Recorder and click **Stop**.

Each action is now a row in the table, with three columns:

| Column | Example | What it means for you |
| --- | --- | --- |
| **Command** | `click`, `type`, `sendKeys` | The action. In Nitros this becomes the step **Operation** |
| **Target** | `id=GlobalSearchBox` | **How the element was found.** This is what you copy |
| **Value** | `CAS-01234` | The text that was typed (if any) |

### 3.3 Choose the best Target

Click a row, then open the **Target** dropdown under the table. Katalon lists **every way it found to locate the element**, for example:

```text
id=GlobalSearchBox
name=search
css=#GlobalSearchBox
//input[@id='GlobalSearchBox']                 (xpath:attributes)
//div[@id='searchLauncher']/div/input          (xpath:idRelative)
//div[3]/div/div[2]/input                      (xpath:position)
```

Use the buttons next to Target to check your choice:

- **Find**: highlights the element on the page, so you can confirm it is the right one.
- **Select**: lets you click any element on the page to fill in Target without recording.

**Pick a target in this order:**

1. **`id=` with a stable ID.** Best, if the ID looks readable and doesn't change (for example `GlobalSearchBox`, `wweLoginUserNameField`).
2. **`xpath:attributes`** using a stable attribute such as `aria-label`, `name` or `data-id`.
3. **`css=`**, if it is short and readable.
4. **Avoid `xpath:position`** (`//div[3]/div/div[2]/…`). It breaks as soon as the page layout changes.

> **How to spot a dynamic (unstable) ID:** it contains long random parts, GUIDs or trailing numbers, for example `id-915f6055-2e07-4276-ae08-2b96c8d02c57-12` or `cancelButton_1735`. Reload the page and use **Find** again. If the ID changed, it's dynamic. Use a **fragment** of it (see [3.4](#34-copy-the-target-into-locatorsxlsx)).

### 3.4 Copy the Target into Locators.xlsx

Every locator is one row in **Locators.xlsx**, either edited in Excel or through **Locators → Add locator** in the web UI:

| Column | What to put in it |
| --- | --- |
| **Name** | Your name for the element, unique, **no spaces**, for example `GlobalSearchBox` |
| **Strategy** | `XPATH`, `ID`, `CSS_SELECTOR`, `NAME`, `CLASS_NAME` or `TAG_NAME` |
| **Match** | `contains`, `starts-with` or `exact` (only used with Strategy `XPATH` and a **Value**) |
| **Attribute** | The attribute the Value is checked against: `id`, `aria-label`, `class`, `title`…, or `text` for the visible text |
| **Value** | The value or fragment. Up to **3 fragments** separated by `\|` (all must match) |
| **Full XPath** | A complete XPath, starting with `//` or `/`. **Raw XPath only** |
| **Notes** | Anything that helps you remember |

> ⚠️ **The most common mistake:** pasting Katalon's Target **as-is** into **Full XPath**. Nitros always runs the Full XPath column as raw XPath, so `id=GlobalSearchBox`, `css=…`, `name=…` or `xpath=//…` there is **invalid and silently ignored**. Convert the target with the table below.

#### Conversion table: Katalon Target → Locators.xlsx

| Katalon Target | Strategy | Match | Attribute | Value | Full XPath |
| --- | --- | --- | --- | --- | --- |
| `id=GlobalSearchBox` (stable) | `ID` | *(blank)* | *(blank)* | `GlobalSearchBox` | *(blank)* |
| `name=search` | `NAME` | | | `search` | |
| `css=#GlobalSearchBox` | `CSS_SELECTOR` | | | `#GlobalSearchBox` | |
| `link=Add note and close` | `XPATH` | `exact` | `text` | `Add note and close` | |
| `//input[@aria-label='Mobile Phone']` | `XPATH` | `exact` | `aria-label` | `Mobile Phone` | *(or paste the whole XPath here instead)* |
| `xpath=//button[@title='Save']` | `XPATH` | | | | `//button[@title='Save']` ← **remove `xpath=`** |
| `id=id-915f6055-2e07-…-12` (dynamic) | `XPATH` | `starts-with` | `id` | `id-915f6055-2e07-4276-ae08-2b96c8d02c57` | *(blank)* |
| `id=lvdcg.incident.TimeTrackingCheckOut.Command.ab12` (dynamic tail) | `XPATH` | `contains` | `id` | `lvdcg.incident.TimeTrackingCheckOut.Command.` | *(blank)* |

**Worked example 1: a stable ID.** Katalon shows `id=wweLoginUserNameField`.
→ Name `DialerLoginUser`, Strategy `ID`, Value `wweLoginUserNameField`. Everything else blank.

**Worked example 2: a dynamic ID.** Katalon shows `id=notescontrol-createNewRecord_flyoutMenuItem_lvidg_sms_4417`. The ending `_4417` changes on every page load.
→ Name `FlyoutMenuItemSMS`, Strategy `XPATH`, Match `contains`, Attribute `id`, Value `notescontrol-createNewRecord_flyoutMenuItem_lvidg_sms`.
Nitros builds `//*[contains(@id,'notescontrol-createNewRecord_flyoutMenuItem_lvidg_sms')]`.

**Worked example 3: several fragments.** If one fragment matches too many elements, add up to three, separated by `|`:
Value `timeline | highlights | content` → `//*[contains(@id,'timeline') and contains(@id,'highlights') and contains(@id,'content')]`.

**Worked example 4: by visible text.** A button labeled *Add note and close*:
→ Strategy `XPATH`, Match `exact`, Attribute `text`, Value `Add note and close`.

> **Tip: the "Fill from Full XPath" button.** In the Locators tab's edit form, paste an XPath that contains `@id='…'` (for example `//*[@id="sec_tab_contact-associatedEntityRecordName-23"]`) into **Full XPath** and click **Fill from Full XPath**. The tool removes the trailing number, splits the ID into up to 3 fragments in **Value**, sets Attribute `id` and Match `contains`. Then clear the Full XPath box if you only want the fragment match. The preview under the form shows the exact XPath for each match type.

#### How Nitros looks for an element

For each locator, Nitros tries these in order and uses the **first visible match**. It keeps retrying for about 10 seconds.

1. **Full XPath**, if filled in.
2. If Strategy is **not** XPATH: the **Value** with that strategy (ID, NAME, CSS…).
3. If Strategy is XPATH: the **Value** with the saved **Match**, then the other two match types.

When a different match type works than the one saved, Nitros **writes the working one back into the Match column** (see the log line `matched with 'contains' … saving`). Over time your sheet improves itself, but only if Excel isn't holding the file open.

### 3.5 Alternative: Chrome DevTools (no extension)

1. Right-click the element → **Inspect**. DevTools opens with the element's HTML highlighted.
2. Read the attributes directly (`id="…"`, `aria-label="…"`, `name="…"`).
3. Or right-click the highlighted HTML → **Copy → Copy XPath** (short, often ID-based) or **Copy full XPath** (long, position-based, which breaks easily). Paste it into **Full XPath** as-is; DevTools XPaths have no prefix.

### 3.6 Test a locator before using it

In DevTools open the **Console** tab and type:

```javascript
$x("//*[contains(@id,'GlobalSearchBox')]")
```

- `[input#GlobalSearchBox]` (exactly **one** result): good.
- `[]` (empty): the XPath is wrong, or the element is inside an iframe or a not-yet-opened panel.
- Several results: add another fragment (`|`) or use a more specific attribute.

For CSS, use `document.querySelectorAll("#GlobalSearchBox")`.

---

## 4. Tour of the web UI

Start the app (with the virtual environment active):

```powershell
python web/app.py
```

Your browser opens **http://127.0.0.1:5057** automatically. Keep the PowerShell window open while you use the tool; closing it stops the app. The tabs are meant to be used from left to right.

### 4.1 Setup

| Section | Field | Notes |
| --- | --- | --- |
| Genesys | User, Password, Place ID | Saved to **Windows Credential Manager**, never to a file. **Required to start a run**, even if you don't use a dialer. If you don't, type any placeholder (for example `none`) in all three. Password: leave blank to keep the saved one |
| Agent | Display name | Used for `{agent_name}` in messages |
| Workbooks | Locators.xlsx, Cases.xlsx | Paths to your sheets. The copy buttons copy the path |
| Endpoints | CRM | **Required.** Your Dynamics URL, for example `https://<your-org>.crm.dynamics.com` |
| Endpoints | Dialer | Your Genesys WWE login page (only needed for dialer flows) |
| Chrome | User data folder, Profile folder | Leave **User data folder** empty to use a dedicated profile in `data/chrome_profile` (recommended) |

Click **Save setup**. Settings go to `data/config.json`.

### 4.2 Locators

A searchable list of every row in Locators.xlsx. **Add locator** opens a form with the same columns as the sheet (see [3.4](#34-copy-the-target-into-locatorsxlsx)), plus a live XPath preview and the **Fill from Full XPath** helper. Changes are written straight to the Excel file, so **close Locators.xlsx in Excel first**.

### 4.3 Templates

Plain-text messages with placeholders in braces. A starter template `SMS_1` is created automatically:

```text
Hello {CX_name}, Please reply with 1, 2, or 3 regarding your recent service request for case {case_number}.
...
- {agent_name}
```

**Available placeholders:**

| Placeholder | Comes from |
| --- | --- |
| `{case_number}` | Column **Case Number** in Cases.xlsx |
| `{notes}` | Column **Notes** in Cases.xlsx |
| `{agent_name}` | Setup → Display name |
| `{dialer_url}` | Setup → Dialer |
| `{genesys_user}`, `{genesys_password}`, `{genesys_place}` | Setup → Genesys |
| Any scrape variable, for example `{CX_name}` | A **Scrape into variable** step earlier in the flow |

> If a placeholder has no value when the step runs (for example `{CX_name}` used before the scrape step), the step fails with **"variable 'CX_name' has no value"**.

Template names may only use letters, numbers, spaces, `_` and `-`.

### 4.4 Flows

Choose a flow on the left, or **New flow** (name plus category, for example *Setup*, *Case* or *Communication*). Click **Add step** and fill in:

| Field | Meaning |
| --- | --- |
| **Label** | A description that appears in the log, for example "Open first result" |
| **Operation** | What to do (see the table below) |
| **Item (locator name)** | The locator **Name** from Locators.xlsx (it autocompletes) |
| **Value** | Text, a URL or a variable name, depending on the operation. Placeholders allowed |
| **Template** | For typing operations: a template to type instead of Value |
| **Wait after step (seconds)** | A pause after the step so the page can load. For *Wait until element appears* it is the **timeout** instead |

**Operations:**

| Operation (UI name) | Item | Value | What happens |
| --- | --- | --- | --- |
| **Click** | ✅ | – | Clicks the element |
| **Send keys** | ✅ | text / `{var}` (or Template) | Types the text into the element |
| **Send keys + Enter** | ✅ | text / `{var}` (or Template) | Types the text, then presses Enter |
| **Scrape into variable** | – | variable name, for example `CX_name` | Reads the value defined in **Scrape data** and stores it |
| **Navigate to URL (this tab)** | – | URL | Opens the URL in the current tab |
| **Open URL in a new tab** | – | URL, for example `{dialer_url}` | Opens a new tab, keeping the CRM tab |
| **Switch to tab (address contains)** | – | part of a URL, for example `crm.dynamics` | Switches to the first tab whose address contains the text |
| **Wait until element appears (login check)** | ✅ | – | Waits up to *Wait* seconds (300 if empty) for the element. Used for the first login |
| **Run another flow** | – | (choose a flow) | Runs a whole flow as one step, so you can reuse flows |

Use the arrows to reorder steps, then click **Save flows**. A flow can't call itself, directly or through another flow; saving is refused if it does.

### 4.5 Scrape data

Defines **what a Scrape step reads**. Click **Add variable**:

| Field | Example | Meaning |
| --- | --- | --- |
| Variable name | `CX_name` | The name you use as `{CX_name}` and in the scrape step's Value |
| Locator name | `CustomerNameAnchor` | The element to read |
| Read from | `text` or `aria-label` | `text` = visible text. Any other word is read as an HTML attribute (`value`, `title`, `aria-label`…) |
| Transform | Title case | Optional: `JOHN SMITH` → `John Smith` |
| Default if empty | `Our Valued Customer` | Used if the element is missing or empty |

Click **Save variables**.

### 4.6 Run

| Field | Meaning |
| --- | --- |
| Setup flow (runs once) | Optional, for example *Dialer login* or *CRM login check* |
| Case flow (runs for each case) | Required, for example *Search and open case* |
| Cases | How many case numbers were found in Cases.xlsx |
| Progress | Current case, total and failures |

**Run automation** starts the run, **Stop** ends it. The **Live log** shows each step as it runs (turn auto-scroll on or off with the switch).

---

## 5. Your first run, step by step

The goal of the first run is to prove the full chain works on **one or two cases** using the built-in flow **Search and open case** (search the case → open it → read the customer name). It doesn't change any data in the CRM.

### Step 1: Start the app

```powershell
cd <path>\Nitros_Automation
.venv\Scripts\Activate.ps1
python web/app.py
```

The browser opens **http://127.0.0.1:5057**. Leave the PowerShell window open.

### Step 2: Fill in Setup

1. Open the **Setup** tab.
2. **CRM:** your Dynamics 365 URL (copy it from the address bar when you're on the CRM home page).
3. **Display name:** your name as it should appear in messages.
4. **Genesys User / Password / Place ID:** your dialer login, or `none` in all three if you won't use the dialer.
5. Leave **Chrome → User data folder** empty.
6. Click **Save setup**. The *Saved* label appears next to Genesys.

### Step 3: Add test case numbers

1. Open `excel\Cases.xlsx` in Excel.
2. Type **one or two real case numbers** in column **A (Case Number)**, starting at row 2. Leave Notes empty.
3. **Save and close** Excel. Nitros can't update files that Excel has open.

### Step 4: Check the three locators this flow uses

The sample flow uses `GlobalSearchBox`, `FirstSearchResult` and `CustomerNameAnchor`. Your CRM may use different IDs, so confirm each one:

1. Open the CRM in your normal Chrome.
2. Use **Katalon Recorder** ([3.2](#32-record-an-element)): Record → click the search box → type a case number → click the first result → Stop.
3. Compare each Target with the row in the **Locators** tab and fix it if needed with the [conversion table](#conversion-table-katalon-target--locatorsxlsx).
4. **Important:** open `GlobalSearchBox` in the Locators tab. If **Full XPath** contains `id=GlobalSearchBox`, **clear that box** (it isn't a valid XPath) and make sure Strategy is `ID` and Value is `GlobalSearchBox`, or whatever your Target shows.
5. For the customer name: open a case, use **Select** or DevTools on the customer name link in the case header, and check that `CustomerNameAnchor` matches it. The scrape variable `CX_name` reads its `aria-label`.

### Step 5: Add a login wait (recommended for the first run)

On the first run Chrome opens with a **brand-new profile**, so you must log in to the CRM by hand. To make the run wait for you:

1. **Flows → New flow**, name `CRM login check`, category `Setup`.
2. **Add step**: Label `Wait for CRM login`, Operation **Wait until element appears (login check)**, Item `GlobalSearchBox`, Wait `300`.
3. **Save flows**.

The run will now wait up to 5 minutes for the search box, which only appears once you've logged in.

### Step 6: Start the run

1. Open the **Run** tab.
2. **Setup flow:** `CRM login check`.
3. **Case flow:** `Search and open case`.
4. Check that **Cases** shows the number you entered (1 or 2).
5. Click **Run automation**.

### Step 7: Log in to the CRM in the new Chrome window

A new Chrome window opens, labeled *"Chrome is being controlled by automated test software"*. That's expected.

1. The log says: `First session: this Chrome profile is new. Log in to CRM in the browser window; the run waits for you.`
2. **Sign in to the CRM in that window** (including MFA). Tick *Stay signed in* if you're offered it.
3. Once the CRM home page loads, the search box appears and the run continues by itself.
4. **Don't use the mouse or keyboard in the automated window** while it runs. You can use other windows.

Later runs reuse this profile (`Existing Chrome profile found, reusing its saved login.`), so you usually won't need to log in again.

### Step 8: Read the log

A successful run looks like this:

```text
2026-11-05 09:00:01  Loaded 55 locators and 2 cases
2026-11-05 09:00:01  First session: this Chrome profile is new. Log in to CRM in the browser window; the run waits for you.
2026-11-05 09:00:05  Flow 'CRM login check' (1 steps)
2026-11-05 09:00:05    [1] Wait for CRM login
2026-11-05 09:00:05      waiting up to 300s for 'GlobalSearchBox' to appear
2026-11-05 09:01:12  === Case 1/2: CAS-01234-ABCDE
2026-11-05 09:01:12  Flow 'Search and open case' (4 steps)
2026-11-05 09:01:12    [1] click on search box
2026-11-05 09:01:15    [2] send case number
2026-11-05 09:01:20    [3] Open first result
2026-11-05 09:01:22    [4] Read customer name
2026-11-05 09:01:22      CX_name = John Smith
2026-11-05 09:01:22      OK
...
2026-11-05 09:02:05  Finished: 2 succeeded, 0 failed
```

| You see | Meaning |
| --- | --- |
| `OK` after a case | Every step worked |
| `CX_name = Our Valued Customer` | The name element wasn't found, so the default was used. Check `CustomerNameAnchor` |
| `[FAILED] step 3 'Open first result': element 'FirstSearchResult' not found` | Fix that locator. A screenshot is saved in `data\logs\errors\` |
| `matched with 'starts-with' (saved: 'contains'), saving` | Not an error: Nitros found a better match type and saved it |

The full log is in `data\logs\run.log`. When the run finishes, Chrome closes by itself.

🎉 **If both cases show `OK`, your setup works.** Next: build a real automation ([section 6](#6-build-your-own-automation-worked-example)), and add the *Dialer login* setup flow if you use Genesys.

---

## 6. Build your own automation (worked example)

**Goal:** for every case, add a **note** saying the customer was contacted.

### 6.1 Plan the clicks

Do the task once by hand and write down every action:

1. Search the case and open it. (There is already a flow for this: *Search and open case*.)
2. Click the **+** in the timeline.
3. Click **Note**.
4. Type the note text.
5. Click **Add note and close**.

### 6.2 Record the elements with Katalon Recorder

1. Open a test case in the CRM.
2. Katalon Recorder → **New** → **Record**.
3. Do steps 2–5 above by hand.
4. **Stop**. You now have four rows, each with a Target.
5. For each row, open the Target dropdown, choose the most stable option ([3.3](#33-choose-the-best-target)) and use **Find** to confirm it highlights the right element.
6. **Reload the page and Find again.** If the element isn't found, the ID is dynamic, so use a fragment.

### 6.3 Add the locators

In **Locators → Add locator** (several are already in the sample sheet, so check first):

| Name | Strategy | Match | Attribute | Value |
| --- | --- | --- | --- | --- |
| `AddMenuButton` | XPATH | starts-with | id | *(fragment from Katalon)* |
| `FlyoutMenuItemNotes` | XPATH | contains | id | `notescontrol-createNewRecord_flyoutMenuItem_notes` |
| `NoteEditor` | XPATH | contains | id | `rtev` |
| `NoteAddAndClose` | XPATH | exact | text | `Add note and close` |

### 6.4 Write the template

**Templates → New template**, name `Note_Contacted`:

```text
Contacted {CX_name} regarding case {case_number}. {notes}
- {agent_name}
```

`{notes}` comes from the Notes column in Cases.xlsx, so you can add per-case text.

### 6.5 Build the flow

**Flows → New flow**, name `Add contact note`, category `Case`. Add these steps:

| # | Label | Operation | Item | Value | Template | Wait |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Open the case | Run another flow | | *Search and open case* | | 2 |
| 2 | Open + menu | Click | `AddMenuButton` | | | 1 |
| 3 | Pick Note | Click | `FlyoutMenuItemNotes` | | | 2 |
| 4 | Type note | Send keys | `NoteEditor` | | `Note_Contacted` | 1 |
| 5 | Save note | Click | `NoteAddAndClose` | | | 3 |

Step 1 reuses the existing flow, which also scrapes `{CX_name}`, so the template can use it. Click **Save flows**.

### 6.6 Test, then scale up

1. Put **one** case number in Cases.xlsx and run with **Case flow** `Add contact note`.
2. Watch the automated window and check the note in the CRM.
3. If a step fails, read the error, check the screenshot in `data\logs\errors\`, fix the locator or increase **Wait**.
4. Once it works, add the full list of cases.

### 6.7 Tips for reliable flows

- **Waits:** give the page time after anything that loads (search, opening a record, saving). Start with 2–3 seconds and lower them once the flow is stable.
- **One element, one locator.** If a locator matches several elements, Nitros uses the first *visible* one. Make Values specific.
- **Reuse:** keep small building-block flows (open case, log in) and combine them with **Run another flow**.
- **Dialogs:** Chrome's "connection is not private" page and the Genesys *Integration Enabled* alert are dismissed automatically before every step. Other dialogs (for example *Discard changes*) need their own **Click** step; locators such as `DiscardChangesButton` are in the sample sheet.

---

## 7. Run from the command line

Everything the **Run** tab does can be started from PowerShell (with the virtual environment active, from the project folder):

```powershell
python -m core.runner --case-flow "Search and open case" --setup-flow "CRM login check"
```

| Argument | Required | Meaning |
| --- | :---: | --- |
| `--case-flow` | ✅ | Flow name (exactly as in the Flows tab) run for every case |
| `--setup-flow` | ❌ | Flow run once before the cases |

Output is printed to the window. Settings, credentials, flows and sheets are the same ones the web UI uses.

---

## 8. Troubleshooting

| Problem / message | Cause | Fix |
| --- | --- | --- |
| `Save the Genesys user, password and place ID in the Setup tab first` | No credentials in the keyring | Fill all three in **Setup** (placeholders are fine if you don't use a dialer) and save |
| `CRM URL is not set` | Setup → CRM is empty | Enter it and **Save setup** |
| `element 'X' not found` | The locator doesn't match the page, or the page wasn't ready | Check with Katalon **Find** or `$x()`. Increase the previous step's **Wait**. Look at the screenshot in `data\logs\errors\` |
| A locator never matches, even though it looks right | A Katalon prefix (`id=`, `css=`, `xpath=`) was pasted into **Full XPath** | Clear Full XPath or remove the prefix. See [3.4](#34-copy-the-target-into-locatorsxlsx) |
| `locator 'X' is not in Locators.xlsx` | Typo in the step's Item, or the name differs | Use the autocomplete in the step form. Names are case-sensitive |
| `[WARN] Locators.xlsx is open in Excel, match type not saved` | Excel is locking the file | Close Excel. The run continues anyway |
| `variable 'X' has no value` | A `{placeholder}` was used before a scrape step set it, or it is misspelled | Add the scrape step earlier, or fix the spelling (case-sensitive) |
| `scrape variable 'X' is not defined in the Scrape data tab` | The scrape step's Value doesn't match a variable | Add it in **Scrape data** or fix the name |
| `Flow calls itself` | A *Run another flow* loop | Remove the loop |
| `An automation run is already in progress` | A run is still going | Wait, or click **Stop** |
| `'GlobalSearchBox' did not appear within 300s` | You didn't log in in time, or the locator is wrong | Run again and log in sooner. Verify the locator |
| Chrome fails to start / "user data directory is already in use" | You set **User data folder** to your normal Chrome profile while Chrome is open | Close all Chrome windows, or leave the field empty to use the dedicated profile |
| Driver download error on start | No internet or proxy blocking the ChromeDriver download | Connect to the network/VPN and retry. Make sure Chrome is up to date |
| `has no 'Case Number' column` | Header row changed in Cases.xlsx | Recreate it: `python excel/make_templates.py --cases` |
| The run types into the wrong field | The locator matches more than one element | Add a fragment (`a \| b`) or use a more specific attribute |

**Start fresh with the CRM login:** close the app and delete the `data\chrome_profile` folder. The next run is a "first session" again.

---

## 9. Good practice and data safety

- **Test on 1–2 cases** every time you create or change a flow.
- **Close Excel** before running, so match types can be saved and the sheets read.
- **Don't share or commit** `data/config.json`, `data/logs/`, `data/chrome_profile/`, `data/message_templates/` or `excel/Cases.xlsx`. They can contain URLs, case numbers, customer names and your login session. These paths are already git-ignored.
- **Credentials** stay in Windows Credential Manager. Never put passwords in flows, templates or Excel. Use `{genesys_password}` instead.
- **Back up Locators.xlsx** before large edits, and never run `make_templates.py` without `--cases`.
- **Get permission** from your organization before automating its systems, and follow its security and data-handling rules. Nitros is an independent project, not affiliated with Microsoft, Genesys or Katalon.

---

## 10. Quick reference

```powershell
# every session
cd <path>\Nitros_Automation
.venv\Scripts\Activate.ps1
python web/app.py                         # UI at http://127.0.0.1:5057

# one-time / maintenance
pip install -r requirements.txt
python excel/make_templates.py --cases    # new blank Cases.xlsx (keeps Locators.xlsx)

# run without the UI
python -m core.runner --case-flow "Search and open case" --setup-flow "CRM login check"
```

| File / folder | Purpose |
| --- | --- |
| `excel/Locators.xlsx` | Element locators |
| `excel/Cases.xlsx` | Case numbers (column A) and notes |
| `data/flows.json` | Flows |
| `data/scrape_map.json` | Scrape variables |
| `data/message_templates/` | Templates (`.txt`) |
| `data/config.json` | Setup settings |
| `data/logs/run.log` | Run log |
| `data/logs/errors/` | Failure screenshots |
| `data/chrome_profile/` | Saved Chrome login |

**Katalon Target → locator, in one line each:**
`id=X` → ID / `X` · `name=X` → NAME / `X` · `css=X` → CSS_SELECTOR / `X` · `xpath=//…` → Full XPath `//…` · `link=T` → XPATH, exact, text, `T` · dynamic id → XPATH, contains/starts-with, id, stable fragment.
