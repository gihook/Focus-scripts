# Rationaletech CHub Submission Creator

A clean, robust, zero-dependency Python script to create, initialize, and save submissions on the Rationaletech CHub server.

## Features

1. **Local Dynamic Configuration (`.config.json`):** Keep credentials and target hosts safe and local. Securely ignored in `.gitignore` to prevent any secret tracking or leaks.
2. **Dynamic Submission Type Parsing:** Automatically extracts the list of available submission types from the server's initial response and presents them dynamically.
3. **Flexible CLI Controls:**
   - interactive prompt-based walkthroughs (default).
   - full script automation through robust flags.
4. **Step-by-Step Interactive & Error Logs:** Clear execution logs with descriptive feedback on HTTP failures.

---

## Installation & Setup

### 1. Copy Configuration
Copy the template `.config.example.json` into `.config.json`:
```bash
cp .config.example.json .config.json
```

### 2. Configure Credentials
Edit the hidden `.config.json` file with your target `HOST` and authorization `COOKIE`:
```json
{
  "HOST": "https://chub-dev.rationaletech.com",
  "COOKIE": "ai_user=...; .AspNetCore.Antiforgery.xR-qFIVXoIw=...; auth_cookie=...; XSRF-TOKEN=..."
}
```

---

## Usage Guide

Run the script directly from your terminal:
```bash
./create-submission.py [options]
```

### Available Options (Flags)

| Flag | Long Option | Description |
|---|---|---|
| `-y` | `--yes` | Skips the initial target host and authorization cookie confirmation prompt. |
| `-t` | `--title <title>` | Directly specifies the submission title, skipping the interactive title prompt. |
| `-s` | `--type <id_or_label>` | Directly specifies the submission type using either its ID or case-insensitive Label, skipping the interactive type selection prompt. |

---

## Usage Examples

### 1. Fully Interactive Mode (Default)
Walks you through confirming your credentials, selecting from the available server-provided submission types, and inputting your custom title:
```bash
./create-submission.py
```

### 2. Custom Title Only
Directly sets the submission title but prompts you to confirm credentials and select a submission type:
```bash
./create-submission.py -t "Project Alpha Plan"
```

### 3. Skip Configuration Confirmation
Bypasses the host and cookie confirmation prompt, but still guides you through type selection and title inputs:
```bash
./create-submission.py -y
```

### 4. Fully Automated Execution (No Prompts)
Perfect for CI/CD, scripting, or instant creation. Instantly generates the submission without showing any prompts or requiring user inputs:
```bash
./create-submission.py -y -t "Automated Promotion Request" -s 108
```
*(You can specify types by ID like `108` or by their label like `"Promotion Requests"`).*

---

## Workflow Steps

1. **[1/3] Create Submission:** Calls `/submissions/create` to retrieve a unique UUID for the submission and dynamically reads available type choices.
2. **[2/3] Set Submission Type:** Sends type information (`typeId`) to the server (`/submissions/<id>/save-form-data`).
3. **[3/3] Submit Form Data:** Reads native `save-submission-data.json`, overrides the `title` field with your specified/prompted title, and saves the final form data payload.
4. **Success Output:** Outputs a direct link to the created submission:
   `https://<host>/#/submissions/<submission_id>`
