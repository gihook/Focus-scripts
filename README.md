# Focus Scripts (Rationaletech CHub Helpers)

A clean, robust, modular suite of Python scripts wrapped under a single, unified CLI interface (`./run`) to automate, create, initialize, browse, and execute workflow actions on **Submissions** and **Meetings** on the Rationaletech CHub server.

---

## Workspace Layout
```
.
├── .config.json               # Local target HOST & USERS config (hidden, untracked)
├── .config.example.json       # Template for local config (tracked)
├── .gitignore                 # Extensively configures untracked files
├── README.md                  # This documentation
├── run                        # UNIFIED CLI APP ENTRYPOINT
├── login.py                   # Automated OIDC session login helper
├── src/                       # SHARD MODULAR SOURCE PACKAGE (Standard src/ layout)
│   ├── __init__.py            # Package initialization marker
│   ├── utils.py               # Shared utility facade
│   ├── config_loader.py       # Configuration and account selector helpers
│   ├── form_parser.py         # Metadata form parser helpers
│   ├── http_client.py         # HTTP redirection and session helpers
│   ├── ui_renderer.py         # Screen renders, headers, footers, workflows
│   ├── create_meeting.py      # Meeting creation handler
│   ├── create_submission.py   # Submission creation handler
│   ├── list_meetings.py       # Meeting search & execution CLI
│   ├── list_submissions.py    # Submission search & execution CLI
│   └── list_users.py          # User search & authentication CLI
├── submission-payloads/       # Custom payloads folder for Submissions
│   └── 101.json               # Schema payload for Submission Type ID 101
└── meeting-payloads/          # Custom payloads folder for Meetings
    ├── default.json           # Default fallback template for meetings
    └── 101.json               # Schema payload for Meeting Type ID 101
```

---

## 🚀 The `./run` Unified CLI Entrypoint

All console activities can be invoked through a single executable `./run`. To explore all capabilities and commands, run:
```bash
./run --help
```

### Main Commands:
* **Create a Submission:** `(Shortcut: ./run s c)`
  ```bash
  ./run submission create [options]
  ```
* **Browse & Search Submissions:** `(Shortcut: ./run s l)`
  ```bash
  ./run submission list [options]
  ```
* **Direct Submission Lookup (by UUID or Display ID):** `(Shortcut: ./run s <id_or_uuid>)`
  ```bash
  ./run submission <id_or_uuid> [options]
  ```
* **Create a Meeting:** `(Shortcut: ./run m c)`
  ```bash
  ./run meeting create [options]
  ```
* **Browse & Search Meetings:** `(Shortcut: ./run m l)`
  ```bash
  ./run meeting list [options]
  ```
* **Direct Meeting Lookup (by UUID or Display ID):** `(Shortcut: ./run m <id_or_uuid>)`
  ```bash
  ./run meeting <id_or_uuid> [options]
  ```
* **Browse & Auth System Users:** `(Shortcut: ./run u l)`
  ```bash
  ./run user list [options]
  ```

*Note: All actions, commands, and options accept a **`--help`** flag dynamically to display up-to-date options without duplicating help data in this document (e.g. `./run submission create --help`).*

---

## 🌟 Modern Terminal Screen Experience & Advanced Features

The suite features a robust, console-native experience that transforms simple scrolling logs into unified, full-screen console dashboards.

### 1. Persistent Header & Footer Dashboard Layout
The interactive list/search scripts (`./run meeting list`, `./run submission list`, and `./run user list`) treat the console as a screen application:
- **Automatic Screen Clears:** Terminal clears dynamically on redraws (pagination, searches, details views) to keep output clean and readable.
- **Inverted ANSI Colors:** Displays high-contrast, bold, reverse-video headers and footers that automatically adapt to your terminal's theme (dark or light mode).
- **Session Status:** The top header lists the active server host, while the persistent footer displays the active logged-in user at all times.

### 2. Dynamic, In-View User Switching
When viewing meeting or submission details, you can switch the active logged-in session on the fly:
- Simply type **`u`** at the action selection prompt.
- Select from any of the already logged-in users saved in your configuration.
- The session re-binds HTTP headers and cookies dynamically, clears the screen, and immediately refreshes the view showing the new user's actions and vote details (`myVote`).

### 3. Detailed ASCII Workflow Pathway Maps
Both meetings and submissions now automatically draw their entire workflow progression step-by-step:
- Shows stage labels, user full names, and current status (`COMPLETE`, `ACTIVE`, `PENDING`).
- Current active stage highlighted prominently with ` ▶ `.
- Connects stages with clean vertical arrows (`↓`) for clear visualization.

### 4. Custom User Config Identification
User auth credentials are saved under their **Full Name and Role** (e.g. `John Doe (HR Member)`) instead of raw emails inside the `USERNAME` field of `.config.json`. This makes selection screens highly readable.

---

## Installation & Setup

### 1. Copy Configuration Template
Copy `.config.example.json` into `.config.json`:
```bash
cp .config.example.json .config.json
```

### 2. Login & Retrieve Cookies Automatically (`login.py`)
Instead of copying cookies manually from your browser, you can log in directly from your terminal using `login.py`!
* Run the login helper:
  ```bash
  ./login.py
  ```
* Enter your email (e.g. `sysadmin` or another authorized email).
* The script automatically completes OIDC authentication against the mock OAuth server, retrieves the target cookies, and populates them directly inside `.config.json` under your email.

Alternatively, log in instantly without prompts by passing the email via flag:
```bash
./login.py -e sysadmin
```

### 3. Browse and Log In as System Users (`./run user list`)
To discover and log in as other system users (such as specific managers, testers, or operators), you can use the interactive users listing script:
* Run the search helper:
  ```bash
  ./run user list
  ```
* Navigating results:
  * Enter `n` to go to the next page, or `p` for the previous page.
  * Enter `s <indices>` to automatically select one or multiple users to log in (e.g. `s 1, 3` or `s 2`).
  * The script dynamically requests mock OIDC tokens, authenticates them, and registers/saves their active credentials inside `.config.json` instantly with their **Full Name & Role**!

### 4. Search and Browse Submissions (`./run submission list`)
To dynamically search, browse, and list submissions inside the CHub workspace:
* Run the listing script:
  ```bash
  ./run submission list
  ```
* Navigating & Filtering results:
  * Enter `n` to go to the next page, or `p` for the previous page.
  * Enter `f <searchTerm>` to filter submissions by a keyword (e.g. `f promotion` or `f draft`).
  * Enter `c` to clear the current search term/filter and reload all results.

Bypass prompts by pre-selecting the user and filter via command line arguments:
```bash
./run submission list -u "John Doe (HR Member)" -q "internal"
```

### 5. Search, Browse, and Execute Meeting Actions (`./run meeting list`)
To dynamically search, browse, view details, and execute actions on meetings inside the CHub workspace:
* Run the meeting browser script:
  ```bash
  ./run meeting list
  ```
* Navigating & Action execution:
  * Enter `n` to go to the next page, or `p` for the previous page.
  * Enter `f <searchTerm>` to filter meetings by keyword.
  * Enter `c` to clear filters.
  * Type any `<number>` matching a meeting to pull up its full details card.
  * Submissions listed inside a meeting card show current **Vote Percentages** and **Your Vote Status** (`myVote`) on the spot.
  * Inside the detail card, select any of the listed `availableActions` (by index number) to fill its parameters and execute it on the spot!
  * Type **`u`** inside the details action listing to dynamically switch sessions!

Bypass prompts and filter directly from arguments:
```bash
./run meeting list -u "John Doe (HR Member)" -q "committee"
```

### 6. Configure Credentials Manually (Optional)
Edit the hidden `.config.json` with your target `HOST` and an array of configured `USERS`:
```json
{
  "HOST": "https://chub-dev.rationaletech.com",
  "USERS": [
    {
      "USERNAME": "John Doe (HR Member)",
      "COOKIE": "ai_user=...; .AspNetCore.Antiforgery.xR-qFIVXoIw=...; auth_cookie=...; XSRF-TOKEN=..."
    },
    {
      "USERNAME": "Jane Doe (HR Member)",
      "COOKIE": "ai_user=...; .AspNetCore.Antiforgery.xR-qFIVXoIw=...; auth_cookie=...; XSRF-TOKEN=..."
    }
  ]
}
```

---

## Multi-User Selection Flow

1. **Interactive Prompt:** If multiple users are configured in `USERS`, running any script will prompt you to select the active user:
   ```
   Available Users:
     [1] John Doe (HR Member)
     [2] Jane Doe (HR Member)
   Select a user [1-2]: 
   ```

2. **Command Line Flag Pre-selection (`-u` / `--user`):** Bypass the selection prompt entirely by pre-selecting the user by name:
   ```bash
   ./run submission create -u "John Doe (HR Member)"
   ```

---

## 1. Submission Creator (`./run submission create`)

Handles creating submissions, dynamically parsing available business units and submission types from the server, selecting/initializing the type, and uploading custom form details.

To see all available command-line options and flag descriptions, run:
```bash
./run submission create --help
```

### Custom Payloads (`submission-payloads/`)
* Put your custom JSON payload as `<typeId>.json` (e.g. `101.json` for *Internal Transfer Requests*).
* If a matching payload is found, it will load it and apply your custom title.
* If not found, it falls back to sending a simple body with only the custom title: `{"title": "..."}`.

---

## 2. Meeting Creator (`./run meeting create`)

Handles creating meetings, dynamically parsing business units and meeting types from the server, initializing the meeting, saving meeting details (Subject and Quorum), and adding available submissions to the meeting agenda.

To see all available command-line options and flag descriptions, run:
```bash
./run meeting create --help
```

### Custom Payloads (`meeting-payloads/`)
* Put your custom JSON payload as `<typeId>.json` (e.g. `101.json` for *Internal*).
* If matching file is missing, the script attempts to load `meeting-payloads/default.json`. If that is also missing, it falls back to `{}`.
* The script dynamically prompts for **Subject** and **Quorum** based on the server's formControls response metadata labels and injects them into the payload.

### Dynamic Submission Agenda Addition
* After saving meeting details, the script automatically fetches available submissions (agenda items) from the server.
* It prints them clearly showing their ID (`displayId`), `subject`, and `typeName`.
* In interactive mode, it prompts you to select multiple items to add to the meeting's agenda.
* It handles list indexing, commas, spaces, and range selections (e.g. `1,3`, `1 3`, `1-2`).

---

## Workflow Examples

### A. Fully Interactive Walkthrough (Meetings)
```bash
./run meeting create
```
This guides you through user selection, choosing the business unit, choosing meeting types, entering meeting details, adding agenda items, and publishing the meeting.

### B. Fully Automated Execution (No Prompts)
Perfect for automation, scripts, or CI/CD pipelines. This runs instantly without prompting for any user input:
```bash
# Automated Submission creation with specific user and business unit
./run submission create -u "John Doe (HR Member)" -y -b "HR Committee" -t "My Automated Submission" -s 101

# Automated Meeting creation with specific user, automatic business unit, meeting type, agenda items, and publication
./run meeting create -u "John Doe (HR Member)" -y -b "HR Committee" -s 101 -t "Sync Meeting" -q "3" -a "1,2" --publish
```
