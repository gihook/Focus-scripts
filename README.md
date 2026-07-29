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

### 2. Configure Credentials
Edit the hidden `.config.json` with your target `HOST` and authorization `COOKIE`:
```json
{
  "HOST": "https://chub-dev.rationaletech.com",
  "COOKIE": "ai_user=...; .AspNetCore.Antiforgery.xR-qFIVXoIw=...; auth_cookie=...; XSRF-TOKEN=..."
}
```

---

## 1. Submission Creator (`create-submission.py`)

Handles creating submissions, dynamically parsing available submission types from the server, selecting/initializing the type, and uploading custom form details.

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
| `-t` | `--title <title>` | Directly specifies the submission title, skipping the title prompt. |
| `-s` | `--type <type>` | Directly specifies the type ID or Label, skipping the type prompt. |

---

## 2. Meeting Creator (`create-meeting.py`)

Handles creating meetings, dynamically parsing meeting types from the server, initializing the meeting, and saving meeting details (Subject and Quorum).

### Custom Payloads (`meeting-payloads/`)
* Put your custom JSON payload as `<typeId>.json` (e.g. `101.json` for *Internal*).
* If matching file is missing, the script attempts to load `meeting-payloads/default.json`. If that is also missing, it falls back to `{}`.
* The script then dynamically prompts for **Subject** and **Quorum** based on the server's formControls response metadata labels and injects them into the payload.

### CLI Usage & Flags
```bash
./create-meeting.py [options]
```

| Flag | Long Option | Description |
|---|---|---|
| `-y` | `--yes` | Bypasses the target host and authorization cookie confirmation prompt. |
| `-s` | `--type <type>` | Directly specifies the meeting type ID or Label, skipping the type prompt. |
| `-t` | `--subject <text>`| Directly specifies the meeting subject, skipping the subject prompt. |
| `-q` | `--quorum <text>` | Directly specifies the meeting quorum, skipping the quorum prompt. |

---

## Workflow Examples

### A. Fully Interactive Walkthrough (Meetings)
```bash
./create-meeting.py
```
This guides you through confirming your credentials, selecting a meeting type from the server-returned choices, and prompting you for your custom subject and quorum.

### B. Fully Automated Execution (No Prompts)
Perfect for automation, scripts, or CI/CD pipelines. This runs instantly without prompting for any user input:
```bash
# Automated Submission creation
./create-submission.py -y -t "My Automated Submission" -s 101

# Automated Meeting creation
./create-meeting.py -y -s 101 -t "Sync Meeting" -q "3"
```
