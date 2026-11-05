<div align="center">

# ⚡ Nitros Automation

**Automate repetitive CRM case work (search, read, message, update) from a simple local web UI.**

[![License](https://img.shields.io/github/license/arahmanjrm/Nitros_Automation?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Issues](https://img.shields.io/github/issues/arahmanjrm/Nitros_Automation?style=flat-square)](https://github.com/arahmanjrm/Nitros_Automation/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](#-contributing)

[Report a Bug](https://github.com/arahmanjrm/Nitros_Automation/issues/new?labels=bug) · [Request a Feature](https://github.com/arahmanjrm/Nitros_Automation/issues/new?labels=enhancement)

</div>

---

## 📑 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#-usage)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)
- [Acknowledgements](#-acknowledgements)
- [Disclaimer](#%EF%B8%8F-disclaimer)

---

## 📖 About

Nitros Automation is a no-code browser automation tool for support agents who work cases in Microsoft Dynamics 365 and a Genesys Workspace Web Edition (WWE) dialer. You describe a task once as a **flow**: a list of steps such as "search case", "click", "type" or "read a field", built in a local web UI. The tool then runs that flow against every case number in an Excel sheet.

**The problem:** Agents repeat the same clicks for every case: search the case number, open it, copy the customer name, open the SMS form, type a standard message, save. This is slow and easy to get wrong.

**The solution:** A Selenium runner driven by editable flows, element locators kept in Excel, and message templates with `{placeholders}` filled from data read off the page.

**Who it's for:** Customer-support and operations agents who handle many similar cases each day.

---

## ✨ Features

- ✅ **Flow builder**: build step-by-step flows in the browser (click, type, type + Enter, open URL, new tab, switch tab, wait for element, scrape, run another flow).
- ✅ **Excel-driven**: element locators live in `Locators.xlsx`, case numbers in `Cases.xlsx`.
- ✅ **Scraping into variables**: read text or attributes from the page (e.g. the customer name) and reuse them in later steps and messages.
- ✅ **Message templates**: plain-text templates with `{CX_name}`, `{case_number}`, `{agent_name}` and any scraped variable.
- ✅ **Secure credentials**: the dialer login is kept in the OS keyring (Windows Credential Manager / macOS Keychain), never in files.
- ✅ **Reusable Chrome session**: a dedicated Chrome profile keeps your CRM login between runs.
- ✅ **Failure screenshots and logs**: every failed step is logged and screenshotted locally.

---

## 🛠 Tech Stack

| Layer              | Technology                   |
| ------------------ | ---------------------------- |
| Language           | Python 3.10+                 |
| Browser automation | Selenium + WebDriver Manager |
| Web UI             | Flask + vanilla JavaScript   |
| Data input/output  | openpyxl (Excel)             |
| Secrets            | keyring                      |
| UI smoke test      | Playwright (optional)        |

---

## 📂 Project Structure

```text
Nitros_Automation/
├── core/                  # Automation engine
│   ├── browser.py         #   Chrome / driver setup
│   ├── config.py          #   Paths and settings
│   ├── credentials.py     #   Keyring credential storage
│   ├── excel_io.py        #   Excel read/write helpers
│   ├── flows.py           #   Flow and scrape-map storage
│   ├── locators.py        #   Element locator helpers
│   ├── runner.py          #   Flow runner (CLI entry point)
│   ├── safe.py            #   Safe/retrying UI actions
│   └── templates.py       #   Message templates
├── web/                   # Local web UI
│   ├── app.py             #   Flask app (entry point)
│   ├── static/            #   CSS and JavaScript
│   ├── templates/         #   index.html
│   └── verify_ui.py       #   Playwright UI smoke check
├── excel/
│   ├── Locators.xlsx      #   Element locators
│   └── make_templates.py  #   Generates blank Excel files
├── data/
│   ├── flows.json         #   Example flows
│   └── scrape_map.json    #   Example scrape variables
├── requirements.txt
├── LICENSE
└── README.md
```

These are created on your machine and are **git-ignored**: `data/config.json`, `data/logs/`, `data/chrome_profile/`, `data/message_templates/` and `excel/Cases.xlsx`.

---

## 🚀 Getting Started

### Prerequisites

- [Python](https://www.python.org/downloads/) **3.10** or newer
- [Google Chrome](https://www.google.com/chrome/) (latest)
- [Git](https://git-scm.com/)
- Access to your own Dynamics 365 CRM and, optionally, a Genesys WWE dialer

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/arahmanjrm/Nitros_Automation.git
   cd Nitros_Automation
   ```

2. **Create and activate a virtual environment**

   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create a blank case sheet**

   ```bash
   python excel/make_templates.py --cases
   ```

5. **[Optional] Install Playwright** (only for `web/verify_ui.py`)

   ```bash
   pip install playwright
   playwright install chromium
   ```

### Configuration

Everything is set in the **Setup** tab of the web UI and saved to `data/config.json` (git-ignored). Credentials go to the OS keyring.

| Setting                | Description                                                       | Default               |
| ---------------------- | ----------------------------------------------------------------- | --------------------- |
| `crm_url`              | Your Dynamics 365 URL, e.g. `https://<your-org>.crm.dynamics.com` | *(empty, required)*   |
| `dialer_url`           | Your Genesys WWE login page                                       | *(empty)*             |
| `agent_name`           | Name used for `{agent_name}` in messages                          | *(empty)*             |
| `locators_path`        | Path to `Locators.xlsx`                                           | `excel/Locators.xlsx` |
| `cases_path`           | Path to `Cases.xlsx`                                              | `excel/Cases.xlsx`    |
| `chrome_user_data_dir` | Chrome "User Data" folder to reuse; empty = `data/chrome_profile` | *(empty)*             |
| `chrome_profile_dir`   | Chrome profile directory name                                     | `Default`             |

> 🔐 **Credentials** (Genesys user, password, place ID) are stored in your operating system's secure keyring, never in plain text or in this repository.

---

## 💻 Usage

### Web UI

```bash
python web/app.py
```

The app opens at **http://127.0.0.1:5057**. Work through the tabs from left to right:

1. **Setup**: enter the CRM and dialer URLs, your agent name and dialer credentials.
2. **Locators**: add or edit the page elements the flows use (stored in `Locators.xlsx`).
3. **Templates**: write message templates with `{placeholders}`.
4. **Flows**: build flows from steps.
5. **Scrape data**: map variables (e.g. `CX_name`) to a locator and attribute.
6. **Run**: pick a case flow (and an optional setup flow such as *Dialer login*) and start. Progress and errors appear in the log.

On the first run Chrome opens with a new profile. Log in to the CRM once and the run continues. Later runs reuse the saved login.

### Command line

```bash
python -m core.runner --case-flow "Search and send SMS" --setup-flow "Dialer login"
```

| Argument       | Required | Description                                                    |
| -------------- | :------: | -------------------------------------------------------------- |
| `--case-flow`  |    ✅    | Flow run once for every case number in `Cases.xlsx`            |
| `--setup-flow` |    ❌    | Flow run once before the cases (e.g. logging in to the dialer) |

### Example

1. Put case numbers in column A of `excel/Cases.xlsx`.
2. In **Run**, choose the *Search and send SMS* flow.
3. For each case, the tool searches for it, opens it, reads the customer name into `{CX_name}`, opens the SMS form, types the `SMS_1` template and saves.
4. Results go to `data/logs/run.log`. Failed steps also save a screenshot in `data/logs/errors/`.

---

## 🗺 Roadmap

- [x] Web UI for setup, locators, templates, flows and scraping
- [x] Excel-driven locators and case lists
- [x] Keyring-based credential storage
- [ ] Conditional steps (if element exists / if variable equals)
- [ ] Write per-case results back to Excel
- [ ] Automated tests

See the [open issues](https://github.com/arahmanjrm/Nitros_Automation/issues) for proposed features and known issues.

---

## 🤝 Contributing

Contributions are welcome.

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m "Add amazing feature"`
4. **Push** the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

**Guidelines**

- Follow PEP 8.
- Keep pull requests focused on a single change.
- **Never commit credentials, browser profiles, logs, screenshots, case lists or any customer data.**

---

## 📄 License

Distributed under the **MIT** License. See [`LICENSE`](LICENSE) for details.

---

## 📬 Contact

GitHub: [@arahmanjrm](https://github.com/arahmanjrm)

Project link: [https://github.com/arahmanjrm/Nitros_Automation](https://github.com/arahmanjrm/Nitros_Automation)

---

## 🙏 Acknowledgements

- [Selenium](https://www.selenium.dev/)
- [Flask](https://flask.palletsprojects.com/)
- [openpyxl](https://openpyxl.readthedocs.io/)
- [keyring](https://github.com/jaraco/keyring)
- [Shields.io](https://shields.io/)

---

## ⚠️ Disclaimer

This is an independent personal project. It is not affiliated with, endorsed by, or supported by Microsoft, Genesys, or any employer or client. It ships no credentials, endpoints or customer data; you supply your own.

This project is provided "as is", without warranty of any kind. You are responsible for making sure your use of this tool follows the terms of service, security policies and data-handling rules of every system it interacts with. Get permission from your organization before automating its systems.

<div align="center">

<sub>Built by <a href="https://github.com/arahmanjrm">@arahmanjrm</a></sub>

</div>
