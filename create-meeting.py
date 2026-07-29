#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

CONFIG_FILE = ".config.json"

class SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req:
            # Copy all custom headers from original request to prevent Cookie dropping on redirect
            for key, val in req.headers.items():
                new_req.add_header(key, val)
            for key, val in req.unredirected_hdrs.items():
                new_req.add_header(key, val)
        return new_req

# Install redirect handler globally to retain Cookie and sensitive headers on redirects
opener = urllib.request.build_opener(SameHostRedirectHandler)
urllib.request.install_opener(opener)

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
    if not host:
        print(f"Error: 'HOST' must be set in '{CONFIG_FILE}'.", file=sys.stderr)
        sys.exit(1)
        
    users = config.get("USERS", [])
    if not users:
        cookie = config.get("COOKIE")
        if cookie:
            users = [{"USERNAME": "Default", "COOKIE": cookie}]
            
    if not users:
        print(f"Error: No valid cookies or users found in '{CONFIG_FILE}'. Please set 'COOKIE' or 'USERS'.", file=sys.stderr)
        sys.exit(1)
        
    return host, users

def select_user(users, preselected_username=None):
    if preselected_username is not None:
        search_term = preselected_username.strip().lower()
        for u in users:
            if u.get("USERNAME", "").lower() == search_term:
                return u.get("USERNAME"), u.get("COOKIE")
        print(f"Error: User '{preselected_username}' not found in configuration.", file=sys.stderr)
        print("Available users are:", file=sys.stderr)
        for u in users:
            print(f"  - {u.get('USERNAME')}", file=sys.stderr)
        sys.exit(1)
        
    # If there is only one user in the config, skip prompt and return it directly
    if len(users) == 1:
        return users[0].get("USERNAME"), users[0].get("COOKIE")
        
    print("Available Users:")
    for index, u in enumerate(users, 1):
        print(f"  [{index}] {u.get('USERNAME')}")
        
    while True:
        try:
            selection = input(f"Select a user [1-{len(users)}]: ").strip()
            if not selection:
                print("Selection cannot be empty. Please enter a number.")
                continue
            idx = int(selection) - 1
            if 0 <= idx < len(users):
                selected_user = users[idx]
                return selected_user.get("USERNAME"), selected_user.get("COOKIE")
            else:
                print(f"Number out of range. Please enter a number between 1 and {len(users)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)

def extract_xsrf_token(cookie_str):
    parts = cookie_str.split(';')
    for part in parts:
        part = part.strip()
        if part.startswith('XSRF-TOKEN='):
            return part[len('XSRF-TOKEN='):]
    return 'CfDJ8B3cU1ZsNd1MirISpSbNJd9xEGENsXFsuDl7V5fCVCB8-pA-dO7yChyFNS8TfS_q_-Gz5K5WJeKA4q_0zrp2HZ0xaXWgMy2fIYPUWiVK851Gk2rDAn-zV9tVPYhlouwMrtmtQPeeP9L-8KxFeDtsLPVuevjpLwWrJjvto0piDPQUVGlit2-AOQK2ByM-LOAYHQ'

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
        help="Specify the meeting type ID or Label directly (skips the type prompt)"
    )
    parser.add_argument(
        '-b', '--unit',
        type=str,
        help="Specify the business unit ID or Label directly (skips the unit prompt)"
    )
    parser.add_argument(
        '-t', '--subject',
        type=str,
        help="Specify the meeting subject directly (skips the subject prompt)"
    )
    parser.add_argument(
        '-q', '--quorum',
        type=str,
        help="Specify the meeting quorum ID or Label directly (skips the quorum prompt)"
    )
    parser.add_argument(
        '-u', '--user',
        type=str,
        help="Specify the USERNAME to use from the configuration (skips the user selection prompt)"
    )
    parser.add_argument(
        '-a', '--add-items',
        type=str,
        help="Comma-separated list of Submission UUIDs, Display IDs, or indices to add automatically (skips prompt)"
    )
    parser.add_argument(
        '-p', '--publish',
        action='store_true',
        help="Automatically publish the meeting (skips publish prompt)"
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

def extract_unit_options(create_response):
    form_sections = create_response.get("formSections", [])
    for section in form_sections:
        controls = section.get("formControls", [])
        for ctrl in controls:
            if ctrl.get("key") == "unitId":
                props = ctrl.get("props", {})
                return props.get("options", [])
    return []

def extract_quorum_options(create_response):
    form_sections = create_response.get("formSections", [])
    for section in form_sections:
        controls = section.get("formControls", [])
        for ctrl in controls:
            if ctrl.get("key") == "quorum":
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
    
    # Load configuration details
    host, users = load_config()

    # Select the active user credentials
    username, cookie = select_user(users, args.user)
    print(f"-> Active User: {username}")

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
        'X-XSRF-TOKEN': extract_xsrf_token(cookie),
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Brave";v="150"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"'
    }

    def make_request(url, data_dict=None, method='POST'):
        if method == 'GET':
            req = urllib.request.Request(url, headers=headers, method='GET')
        else:
            payload = json.dumps(data_dict).encode('utf-8') if data_dict is not None else b'{}'
            req = urllib.request.Request(url, data=payload, headers=headers, method=method)
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

    # Extract Business Unit (unitId) Options from the response
    unit_options = extract_unit_options(res)
    selected_unit_id = None
    selected_unit_label = None

    if args.unit is not None:
        search_term = args.unit.strip().lower()
        for option in unit_options:
            if str(option.get('id')) == search_term or str(option.get('label', '')).lower() == search_term:
                selected_unit_id = option.get('id')
                selected_unit_label = option.get('label')
                break
        
        if selected_unit_id is None:
            print(f"\nError: Invalid business unit '{args.unit}' specified.", file=sys.stderr)
            print("Available options are:", file=sys.stderr)
            for opt in unit_options:
                print(f"  ID: {opt.get('id')}  -  '{opt.get('label')}'", file=sys.stderr)
            sys.exit(1)
    else:
        if unit_options:
            if len(unit_options) == 1:
                # Select automatically with no prompt if only one option exists
                selected_unit_id = unit_options[0].get('id')
                selected_unit_label = unit_options[0].get('label')
                print(f" -> Automatically selected single available Business Unit: {selected_unit_label} (ID: {selected_unit_id})")
            else:
                print("\nAvailable Business Units:")
                for index, option in enumerate(unit_options, 1):
                    print(f"  [{index}] {option.get('label')} (ID: {option.get('id')})")
                
                while True:
                    try:
                        selection = input(f"Select a business unit [1-{len(unit_options)}]: ").strip()
                        if not selection:
                            print("Selection cannot be empty. Please enter a number.")
                            continue
                        idx = int(selection) - 1
                        if 0 <= idx < len(unit_options):
                            selected_option = unit_options[idx]
                            selected_unit_id = selected_option.get('id')
                            selected_unit_label = selected_option.get('label')
                            break
                        else:
                            print(f"Number out of range. Please enter a number between 1 and {len(unit_options)}.")
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
                    except (KeyboardInterrupt, EOFError):
                        print("\nOperation cancelled by user.")
                        sys.exit(0)
        else:
            print("\nWarning: No business unit options found in server response.")

    if selected_unit_label:
        print(f" -> Selected Business Unit: {selected_unit_label} (ID: {selected_unit_id})")

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

    # 2. Second Request: Save Form Data (Set Meeting Type and Business Unit)
    print("\n[2/3] Initializing meeting configuration on server...")
    set_type_url = f"{host}/meetings/{meeting_id}/save-form-data"
    type_data = {
        "typeId": selected_type_id,
        "typeId__listItems": [
            {"id": selected_type_id, "label": selected_type_label}
        ]
    }
    if selected_unit_id is not None:
        type_data["unitId"] = selected_unit_id
        type_data["unitId__listItems"] = [
            {"id": selected_unit_id, "label": selected_unit_label}
        ]
    make_request(set_type_url, data_dict=type_data)
    print(" -> Success! Meeting type and business unit initialized.")

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
    quorum_options = extract_quorum_options(res)
    
    selected_quorum_id = None
    selected_quorum_label = None

    if args.quorum is not None:
        search_term = args.quorum.strip().lower()
        for option in quorum_options:
            if str(option.get('id')) == search_term or str(option.get('label', '')).lower() == search_term:
                selected_quorum_id = option.get('id')
                selected_quorum_label = option.get('label')
                break
        
        # If not matched, treat argument as direct raw value
        if selected_quorum_id is None:
            selected_quorum_id = args.quorum.strip()
            selected_quorum_label = args.quorum.strip()
    else:
        if quorum_options:
            print(f"\nAvailable {quorum_label} Options:")
            for index, option in enumerate(quorum_options, 1):
                print(f"  [{index}] {option.get('label')} (ID: {option.get('id')})")
            
            while True:
                try:
                    selection = input(f"Select quorum [1-{len(quorum_options)}]: ").strip()
                    if not selection:
                        print("Selection cannot be empty. Please enter a number.")
                        continue
                    idx = int(selection) - 1
                    if 0 <= idx < len(quorum_options):
                        selected_option = quorum_options[idx]
                        selected_quorum_id = selected_option.get('id')
                        selected_quorum_label = selected_option.get('label')
                        break
                    else:
                        print(f"Number out of range. Please enter a number between 1 and {len(quorum_options)}.")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
                except (KeyboardInterrupt, EOFError):
                    print("\nOperation cancelled by user.")
                    sys.exit(0)
        else:
            try:
                selected_quorum_id = input(f"\nEnter {quorum_label.lower()} for this meeting: ").strip()
                selected_quorum_label = selected_quorum_id
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled by user.")
                sys.exit(0)

    print(f" -> Selected Quorum: {selected_quorum_label} (ID: {selected_quorum_id})")

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
    meeting_data['quorum'] = selected_quorum_id
    meeting_data['quorum__listItems'] = [
        {"id": selected_quorum_id, "label": selected_quorum_label}
    ]

    print(" -> Submitting updated meeting form data payload...")
    save_url = f"{host}/meetings/{meeting_id}/save-form-data"
    make_request(save_url, data_dict=meeting_data)
    print(" -> Success! Meeting details saved.")

    # 4. Prompt to add submission to meeting
    print("\nChecking for available submissions to add to this meeting...")
    available_items_url = f"{host}/meetings/{meeting_id}/available-agenda-items?pageNumber=1&pageSize=10"
    res_items = make_request(available_items_url, method='GET')
    
    # Robustly extract list of items
    items = []
    if isinstance(res_items, list):
        items = res_items
    elif isinstance(res_items, dict):
        items = res_items.get('items', res_items.get('results', res_items.get('data', [])))
        if not items:
            # Fallback check
            for val in res_items.values():
                if isinstance(val, list) and all(isinstance(x, dict) for x in val):
                    items = val
                    break
                    
    if items:
        selected_uuids = []
        if args.add_items is not None:
            # Handle automatic selection from flags
            search_terms = [t.strip().lower() for t in args.add_items.replace(',', ' ').split()]
            for term in search_terms:
                matched = False
                # Try matching by index (1-based)
                try:
                    idx = int(term) - 1
                    if 0 <= idx < len(items):
                        selected_uuids.append(items[idx].get('id'))
                        matched = True
                except ValueError:
                    pass
                
                if not matched:
                    # Try matching by displayId or exact UUID
                    for item in items:
                        if str(item.get('displayId')).lower() == term or str(item.get('id')).lower() == term:
                            selected_uuids.append(item.get('id'))
                            matched = True
                            break
            
            # Clean none/null and duplicate values
            selected_uuids = list(set([uid for uid in selected_uuids if uid]))
        else:
            # Interactive selection
            print("\nAvailable Submissions:")
            for index, item in enumerate(items, 1):
                display_id = item.get('displayId', 'N/A')
                subject = item.get('subject', item.get('title', 'No Subject'))
                type_name = item.get('typeName', item.get('submissionType', {}).get('label', 'N/A'))
                print(f"  [{index}] ID: {display_id} - {subject} ({type_name})")
            
            try:
                selection = input("\nEnter the numbers of the submissions you want to add (e.g. 1, 3) or press Enter to skip: ").strip()
                if selection:
                    # Use robust list selection parser
                    selected_indices = []
                    parts = selection.replace(',', ' ').split()
                    for part in parts:
                        if '-' in part:
                            try:
                                start, end = part.split('-', 1)
                                s_idx = int(start) - 1
                                e_idx = int(end) - 1
                                for i in range(s_idx, e_idx + 1):
                                    if 0 <= i < len(items):
                                        selected_indices.append(i)
                            except ValueError:
                                pass
                        else:
                            try:
                                val = int(part) - 1
                                if 0 <= val < len(items):
                                    selected_indices.append(val)
                            except ValueError:
                                pass
                    
                    # De-duplicate indices preserving order
                    seen = set()
                    unique_indices = [x for x in selected_indices if not (x in seen or seen.add(x))]
                    
                    for idx in unique_indices:
                        selected_uuids.append(items[idx].get('id'))
            except (KeyboardInterrupt, EOFError):
                print("\nSubmissions addition skipped.")
        
        # If we have selected any UUIDs, post them to add-existing-items
        if selected_uuids:
            print(f" -> Adding {len(selected_uuids)} submission(s) to the meeting agenda...")
            add_url = f"{host}/meetings/{meeting_id}/add-existing-items"
            add_data = {
                "aggregateId": meeting_id,
                "placeholderName": "Meeting Agenda",
                "submissionIds": selected_uuids
            }
            make_request(add_url, data_dict=add_data)
            print(" -> Success! Submissions added to meeting agenda.")
        else:
            print(" -> No submissions selected/added.")
    else:
        print(" -> No available submissions found to add to this meeting.")

    # 5. Prompt to publish meeting
    should_publish = False
    if args.publish:
        should_publish = True
    else:
        try:
            confirm_publish = input("\nDo you want to publish this meeting? [y/N]: ").strip().lower()
            should_publish = confirm_publish in ('y', 'yes')
        except (KeyboardInterrupt, EOFError):
            pass

    if should_publish:
        print(" -> Publishing meeting on server...")
        publish_url = f"{host}/meetings/{meeting_id}/execute-workflow-action/PUBLISH"
        make_request(publish_url, data_dict={})
        print(" -> Success! Meeting published.")
    else:
        print(" -> Meeting publication skipped (retains Draft status).")

    # Complete Message
    print("\nMeeting is created.")
    print(f"{host}/#/meetings/{meeting_id}")

if __name__ == '__main__':
    main()
