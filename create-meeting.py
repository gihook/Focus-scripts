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
    parser = argparse.ArgumentParser(description="Create a meeting on Rationaletech CHub.")
    parser.add_argument(
        '-y', '--yes', 
        action='store_true', 
        help="Skip the host and cookie confirmation prompt"
    )
    parser.add_argument(
        '-s', '--type',
        type=str,
        help="Specify the meeting type ID or Label directly (skips the type selection prompt)"
    )
    parser.add_argument(
        '-t', '--subject',
        type=str,
        help="Specify the meeting subject directly (skips the subject prompt)"
    )
    parser.add_argument(
        '-q', '--quorum',
        type=str,
        help="Specify the meeting quorum directly (skips the quorum prompt)"
    )
    return parser.parse_args()

def extract_type_options(create_response):
    form_sections = create_response.get("formSections", [])
    for section in form_sections:
        controls = section.get("formControls", [])
        for ctrl in controls:
            if ctrl.get("key") == "typeId":
                props = ctrl.get("props", {})
                return props.get("options", [])
    return []

def get_control_label(create_response, control_key, default_label):
    form_sections = create_response.get("formSections", [])
    for section in form_sections:
        controls = section.get("formControls", [])
        for ctrl in controls:
            if ctrl.get("key") == control_key:
                props = ctrl.get("props", {})
                return props.get("label", default_label)
    return default_label

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

    # 1. First Request: Create Meeting
    print("[1/3] Creating new meeting on server...")
    create_url = f"{host}/meetings/create"
    res = make_request(create_url, data_dict={})
    
    meeting_id = res.get('id')
    if not meeting_id:
        print(f"\nError: Response from /meetings/create did not contain an 'id'. Response: {res}", file=sys.stderr)
        sys.exit(1)
    print(f" -> Success! Created Meeting ID: {meeting_id}")

    # Extract Meeting Type Options from the response
    options = extract_type_options(res)
    selected_type_id = None
    selected_type_label = None

    if args.type is not None:
        search_term = args.type.strip().lower()
        for option in options:
            if str(option.get('id')) == search_term or str(option.get('label', '')).lower() == search_term:
                selected_type_id = option.get('id')
                selected_type_label = option.get('label')
                break
        
        if selected_type_id is None:
            print(f"\nError: Invalid meeting type '{args.type}' specified.", file=sys.stderr)
            print("Available options are:", file=sys.stderr)
            for opt in options:
                print(f"  ID: {opt.get('id')}  -  '{opt.get('label')}'", file=sys.stderr)
            sys.exit(1)
    else:
        if options:
            print("\nAvailable Meeting Types:")
            for index, option in enumerate(options, 1):
                print(f"  [{index}] {option.get('label')} (ID: {option.get('id')})")
            
            while True:
                try:
                    selection = input(f"Select a type [1-{len(options)}]: ").strip()
                    if not selection:
                        print("Selection cannot be empty. Please enter a number.")
                        continue
                    idx = int(selection) - 1
                    if 0 <= idx < len(options):
                        selected_option = options[idx]
                        selected_type_id = selected_option.get('id')
                        selected_type_label = selected_option.get('label')
                        break
                    else:
                        print(f"Number out of range. Please enter a number between 1 and {len(options)}.")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
                except (KeyboardInterrupt, EOFError):
                    print("\nOperation cancelled by user.")
                    sys.exit(0)
        else:
            # Fallback to default if no options are found
            print("\nWarning: No meeting type options found in server response. Defaulting to type ID 101.")
            selected_type_id = 101
            selected_type_label = "Internal"

    print(f" -> Selected Meeting Type: {selected_type_label} (ID: {selected_type_id})")

    # 2. Second Request: Save Form Data (Set Meeting Type)
    print("\n[2/3] Initializing meeting type on server...")
    set_type_url = f"{host}/meetings/{meeting_id}/save-form-data"
    type_data = {
        "typeId": selected_type_id,
        "typeId__listItems": [
            {"id": selected_type_id, "label": selected_type_label}
        ]
    }
    make_request(set_type_url, data_dict=type_data)
    print(" -> Success! Meeting type initialized.")

    # Determine meeting subject
    subject_label = get_control_label(res, "subject", "Subject")
    if args.subject is not None:
        meeting_subject = args.subject.strip()
    else:
        try:
            meeting_subject = input(f"\nEnter {subject_label.lower()} for this meeting: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user.")
            sys.exit(0)

    # Determine meeting quorum
    quorum_label = get_control_label(res, "quorum", "Quorum")
    if args.quorum is not None:
        meeting_quorum = args.quorum.strip()
    else:
        try:
            meeting_quorum = input(f"Enter {quorum_label.lower()} for this meeting: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user.")
            sys.exit(0)

    # 3. Third Request: Save custom meeting payload
    payload_file = os.path.join("meeting-payloads", f"{selected_type_id}.json")
    print(f"\n[3/3] Preparing meeting form data payload (Type ID: {selected_type_id})...")
    
    if os.path.exists(payload_file):
        print(f" -> Found specific payload file: '{payload_file}'")
        try:
            with open(payload_file, 'r') as f:
                meeting_data = json.load(f)
            print(f" -> Successfully loaded payload from '{payload_file}'")
        except json.JSONDecodeError as e:
            print(f"\nError: Failed to parse JSON from payload file '{payload_file}': {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\nError reading payload file '{payload_file}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Fallback to default.json or empty payload
        default_payload_file = os.path.join("meeting-payloads", "default.json")
        if os.path.exists(default_payload_file):
            print(f" -> Payload '{payload_file}' not found. Loading from generic template '{default_payload_file}'")
            try:
                with open(default_payload_file, 'r') as f:
                    meeting_data = json.load(f)
            except Exception:
                meeting_data = {}
        else:
            print(f" -> No payload file found. Falling back to simple payload.")
            meeting_data = {}

    # Set subject and quorum
    meeting_data['subject'] = meeting_subject
    meeting_data['quorum'] = meeting_quorum

    print(" -> Submitting updated meeting form data payload...")
    save_url = f"{host}/meetings/{meeting_id}/save-form-data"
    make_request(save_url, data_dict=meeting_data)
    print(" -> Success! Meeting details saved.")

    # Complete Message
    print("\nMeeting is created.")
    print(f"{host}/#/meetings/{meeting_id}")

if __name__ == '__main__':
    main()
