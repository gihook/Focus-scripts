# Focus Scripts (Rationaletech CHub Helpers)

A clean, robust, zero-dependency suite of Python scripts to automate, create, initialize, and save **Submissions** and **Meetings** on the Rationaletech CHub server.

---

## Workspace Layout
```
.
├── .config.json               # Local target HOST & COOKIE config (hidden, untracked)
├── .config.example.json       # Template for local config (tracked)
├── .gitignore                 # Extensively configures untracked files
├── README.md                  # This documentation
├── login.py                   # Automated OIDC session login helper
├── list-users.py              # Paginated user browser & terminal-auth helper
├── list-submissions.py        # Paginated submission browser & search filter
├── list-meetings.py           # Paginated meeting browser & search filter
├── create-submission.py       # Submission creation helper
├── create-meeting.py          # Meeting creation helper
├── submission-payloads/       # Custom payloads folder for Submissions
│   └── 101.json               # Schema payload for Submission Type ID 101
└── meeting-payloads/          # Custom payloads folder for Meetings
    ├── default.json           # Default fallback template for meetings
    └── 101.json               # Schema payload for Meeting Type ID 101
```

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
* The script automatically completes OIDC authentication against the mock OAuth server, retrieves the target `auth_cookie`, `XSRF-TOKEN`, and Antiforgery session cookies, and populates them directly inside `.config.json` under your email.

Alternatively, log in instantly without prompts by passing the email via flag:
```bash
./login.py -e sysadmin
```

### 3. Browse and Log In as System Users (`list-users.py`)
To discover and log in as other system users (such as specific managers, testers, or operators), you can use the interactive users listing script:
* Run the search helper (the script prompts you to choose which of your configured accounts should perform the search query):
  ```bash
  ./list-users.py
  ```
* Navigating results:
  * Enter `n` to go to the next page, or `p` for the previous page.
  * Enter `s <indices>` to automatically select one or multiple users to log in (e.g. `s 1, 3` or `s 2`).
  * The script dynamically requests mock OIDC tokens and cookies for the selected users, authenticates them on CHub, and registers/saves their active credentials inside `.config.json` instantly!

### 4. Search and Browse Submissions (`list-submissions.py`)
To dynamically search, browse, and list submissions inside the CHub workspace:
* Run the listing script (the script prompts you to choose which of your configured accounts should perform the query):
  ```bash
  ./list-submissions.py
  ```
* Navigating & Filtering results:
  * Enter `n` to go to the next page, or `p` for the previous page.
  * Enter `f <searchTerm>` to filter submissions by a keyword (e.g. `f promotion` or `f draft`).
  * Enter `c` to clear the current search term/filter and reload all results.

Alternatively, initiate with a pre-selected user and filter directly from command line arguments:
```bash
./list-submissions.py -u SystemAdmin -q "internal"
```

### 5. Search, Browse, and Execute Meeting Actions (`list-meetings.py`)
To dynamically search, browse, view details, and execute actions on meetings inside the CHub workspace:
* Run the meeting browser script:
  ```bash
  ./list-meetings.py
  ```
* Navigating & Action execution:
  * Enter `n` to go to the next page, or `p` for the previous page.
  * Enter `f <searchTerm>` to filter meetings by keyword (e.g. `f committee` or `f draft`).
  * Enter `c` to clear filters.
  * Type any `<number>` matching a meeting to pull up its full details card.
  * Inside the detail card, select any of the listed `availableActions` (by index number) to fill its parameters (supports interactive inputs) and execute it on the spot!

Alternatively, initiate with a pre-selected user and filter directly from arguments:
```bash
./list-meetings.py -u SystemAdmin -q "committee"
```

### 6. Configure Credentials Manually (Optional)
Edit the hidden `.config.json` with your target `HOST` and an array of configured `USERS`:
```json
{
  "HOST": "https://chub-dev.rationaletech.com",
  "USERS": [
    {
      "USERNAME": "SystemAdmin",
      "COOKIE": "ai_user=...; .AspNetCore.Antiforgery.xR-qFIVXoIw=...; auth_cookie=...; XSRF-TOKEN=..."
    },
    {
      "USERNAME": "NormalUser",
      "COOKIE": "ai_user=...; .AspNetCore.Antiforgery.xR-qFIVXoIw=...; auth_cookie=...; XSRF-TOKEN=..."
    }
  ]
}
```

*Note: Backward-compatibility is supported. If your config only has a root-level `"COOKIE"`, the script will automatically treat it as a single user named `"Default"` without prompting you.*

---

## Multi-User Selection Flow

1. **Interactive Prompt:** If multiple users are configured in `USERS`, running any script will prompt you to select the active user:
   ```
   Available Users:
     [1] SystemAdmin
     [2] NormalUser
   Select a user [1-2]: 
   ```
   *(If only one user is configured, the script automatically skips this prompt).*

2. **Command Line Flag Pre-selection (`-u` / `--user`):** Bypass the selection prompt entirely by pre-selecting the user by name:
   ```bash
   ./create-submission.py -u SystemAdmin
   ```

---

## 1. Submission Creator (`create-submission.py`)

Handles creating submissions, dynamically parsing available business units and submission types from the server, selecting/initializing the type, and uploading custom form details.

### Custom Payloads (`submission-payloads/`)
* Put your custom JSON payload as `<typeId>.json` (e.g. `101.json` for *Internal Transfer Requests*).
* If a matching payload is found, it will load it and apply your custom title.
* If not found, it falls back to sending a simple body with only the custom title: `{"title": "..."}`.

### CLI Usage & Flags
```bash
./create-submission.py [options]
```

| Flag | Long Option | Description |
|---|---|---|
| `-y` | `--yes` | Bypasses the target host and authorization cookie confirmation prompt. |
| `-b` | `--unit <unit>` | Directly specifies the business unit ID or Label, skipping the business unit prompt. |
| `-t` | `--title <title>` | Directly specifies the submission title, skipping the title prompt. |
| `-s` | `--type <type>` | Directly specifies the type ID or Label, skipping the type prompt. |
| `-u` | `--user <username>` | Directly specifies which username to select from configuration (skips user prompt). |

---

## 2. Meeting Creator (`create-meeting.py`)

Handles creating meetings, dynamically parsing business units and meeting types from the server, initializing the meeting, saving meeting details (Subject and Quorum), and adding available submissions to the meeting agenda.

### Custom Payloads (`meeting-payloads/`)
* Put your custom JSON payload as `<typeId>.json` (e.g. `101.json` for *Internal*).
* If matching file is missing, the script attempts to load `meeting-payloads/default.json`. If that is also missing, it falls back to `{}`.
* The script dynamically prompts for **Subject** and **Quorum** based on the server's formControls response metadata labels and injects them into the payload.

### Dynamic Submission Agenda Addition
* After saving meeting details, the script automatically fetches available submissions (agenda items) from the server.
* It prints them clearly showing their ID (`displayId`), `subject`, and `typeName`.
* In interactive mode, it prompts you to select multiple items to add to the meeting's agenda.
* It handles list indexing, commas, spaces, and range selections (e.g. `1,3`, `1 3`, `1-2`).

### CLI Usage & Flags
```bash
./create-meeting.py [options]
```

| Flag | Long Option | Description |
|---|---|---|
| `-y` | `--yes` | Bypasses the target host and authorization cookie confirmation prompt. |
| `-b` | `--unit <unit>` | Directly specifies the business unit ID or Label, skipping the business unit prompt. |
| `-s` | `--type <type>` | Directly specifies the meeting type ID or Label, skipping the type prompt. |
| `-t` | `--subject <text>`| Directly specifies the meeting subject, skipping the subject prompt. |
| `-q` | `--quorum <text>` | Directly specifies the meeting quorum, skipping the quorum prompt. |
| `-u` | `--user <username>` | Directly specifies which username to select from configuration (skips user prompt). |
| `-a` | `--add-items <items>`| Comma-separated list of Submission UUIDs, Display IDs, or indices to add automatically (skips prompt). |
| `-p` | `--publish` | Automatically publishes the meeting on the server, bypassing the publication prompt. |

---

## Workflow Examples

### A. Fully Interactive Walkthrough (Meetings)
```bash
./create-meeting.py
```
This guides you through user selection, confirming credentials, choosing the business unit (automatically skipped if only one is available), choosing meeting types, entering meeting details, adding agenda items, and publishing the meeting.

### B. Fully Automated Execution (No Prompts)
Perfect for automation, scripts, or CI/CD pipelines. This runs instantly without prompting for any user input:
```bash
# Automated Submission creation with specific user and business unit
./create-submission.py -u SystemAdmin -y -b "HR Committee" -t "My Automated Submission" -s 101

# Automated Meeting creation with specific user, automatic business unit, meeting type, agenda items, and publication
./create-meeting.py -u NormalUser -y -b "HR Committee" -s 101 -t "Sync Meeting" -q "3" -a "1,2" --publish
```
