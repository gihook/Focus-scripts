#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

CONFIG_FILE = ".config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Configuration file '{CONFIG_FILE}' is missing.", file=sys.stderr)
        print(f"Please copy '.config.example.json' to '{CONFIG_FILE}' and fill in your COOKIE and HOST.", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error: Failed to read or parse '{CONFIG_FILE}': {e}", file=sys.stderr)
        sys.exit(1)
        
    host = config.get("HOST")
    cookie = config.get("COOKIE")
    
    if not host or not cookie:
        print(f"Error: Both 'HOST' and 'COOKIE' must be set in '{CONFIG_FILE}'.", file=sys.stderr)
        sys.exit(1)
        
    return host, cookie

def parse_arguments():
    parser = argparse.ArgumentParser(description="Create a submission on Rationaletech CHub.")
    parser.add_argument(
        '-y', '--yes', 
        action='store_true', 
        help="Skip the host and cookie confirmation prompt"
    )
    parser.add_argument(
        '-t', '--title',
        type=str,
        help="Specify submission title directly (skips the title prompt)"
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Load host and cookie from the hidden config file
    host, cookie = load_config()

    # Show configuration and prompt for confirmation if not skipped via -y/--yes
    print("Configuration details:")
    print(f"  HOST:   {host}")
    truncated_cookie = cookie[:60] + "..." if len(cookie) > 60 else cookie
    print(f"  COOKIE: {truncated_cookie}")
    
    if not args.yes:
        try:
            confirm = input("\nDo you want to proceed with this configuration? [y/N]: ").strip().lower()
            if confirm not in ('y', 'yes'):
                print("Aborted.")
                sys.exit(0)
            print() # Insert newline for nicer output formatting
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Cookie': cookie,
        'X-XSRF-TOKEN': 'CfDJ8B3cU1ZsNd1MirISpSbNJd9xEGENsXFsuDl7V5fCVCB8-pA-dO7yChyFNS8TfS_q_-Gz5K5WJeKA4q_0zrp2HZ0xaXWgMy2fIYPUWiVK851Gk2rDAn-zV9tVPYhlouwMrtmtQPeeP9L-8KxFeDtsLPVuevjpLwWrJjvto0piDPQUVGlit2-AOQK2ByM-LOAYHQ',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Brave";v="150"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"'
    }

    def make_request(url, data_dict=None):
        payload = json.dumps(data_dict).encode('utf-8') if data_dict is not None else b'{}'
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print(f"\nError: HTTP Request to {url} failed with status {e.code}", file=sys.stderr)
            try:
                error_body = e.read().decode('utf-8')
                print(f"Response Body: {error_body}", file=sys.stderr)
            except Exception:
                pass
            sys.exit(1)
        except Exception as e:
            print(f"\nError connecting to {url}: {e}", file=sys.stderr)
            sys.exit(1)

    # 1. First Request: Create Submission
    print("[1/3] Creating new submission on server...")
    create_url = f"{host}/submissions/create"
    res = make_request(create_url, data_dict={})
    
    submission_id = res.get('id')
    if not submission_id:
        print(f"\nError: Response from /submissions/create did not contain an 'id'. Response: {res}", file=sys.stderr)
        sys.exit(1)
    print(f" -> Success! Created Submission ID: {submission_id}")

    # 2. Second Request: Save Form Data (Set Type)
    print("[2/3] Initializing submission type to Internal Transfer Request (ID: 101)...")
    set_type_url = f"{host}/submissions/{submission_id}/save-form-data"
    type_data = {
        "typeId": 101,
        "typeId__listItems": [
            {"id": 105, "label": "New Hire Requests"}
        ]
    }
    make_request(set_type_url, data_dict=type_data)
    print(" -> Success! Submission type initialized.")

    # Determine submission title
    if args.title is not None:
        submission_title = args.title.strip()
    else:
        # Prompt User for Title
        try:
            submission_title = input("\nEnter title for this submission: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user.")
            sys.exit(0)

    # 3. Third Request: Save custom form data
    print(f"[3/3] Reading save-submission-data.json and applying title '{submission_title}'...")
    try:
        with open('save-submission-data.json', 'r') as f:
            submission_data = json.load(f)
    except FileNotFoundError:
        print("\nError: save-submission-data.json not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\nError: Failed to parse save-submission-data.json: {e}", file=sys.stderr)
        sys.exit(1)

    submission_data['title'] = submission_title

    print(" -> Submitting updated form data payload...")
    save_url = f"{host}/submissions/{submission_id}/save-form-data"
    make_request(save_url, data_dict=submission_data)
    print(" -> Success! Submission details saved.")

    # Complete Message
    print("\nSubmission is created.")
    print(f"{host}/#/submissions/{submission_id}")

if __name__ == '__main__':
    main()
