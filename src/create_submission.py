#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

CONFIG_FILE = ".config.json"

from src.utils import (
    select_user, print_user_header, clear_screen, print_app_header, print_app_footer,
    load_config, extract_xsrf_token, extract_type_options, extract_unit_options
)



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
    parser.add_argument(
        '-s', '--type',
        type=str,
        help="Specify the submission type ID or Label directly (skips the type selection prompt)"
    )
    parser.add_argument(
        '-b', '--unit',
        type=str,
        help="Specify the business unit ID or Label directly (skips the unit prompt)"
    )
    parser.add_argument(
        '-u', '--user',
        type=str,
        help="Specify the USERNAME to use from the configuration (skips the user selection prompt)"
    )
    return parser.parse_args()



def main():
    args = parse_arguments()
    
    # Load configuration details
    host, users, _ = load_config()

    # Select the active user credentials
    username, cookie = select_user(users, args.user)
    
    clear_screen()
    print_app_header(host)

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

    # Extract Submission Type Options from the response
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
            print(f"\nError: Invalid submission type '{args.type}' specified.", file=sys.stderr)
            print("Available options are:", file=sys.stderr)
            for opt in options:
                print(f"  ID: {opt.get('id')}  -  '{opt.get('label')}'", file=sys.stderr)
            sys.exit(1)
    else:
        if options:
            print("\nAvailable Submission Types:")
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
            # Fallback to defaults if no options are present in the response
            print("\nWarning: No submission type options found in server response. Defaulting to Internal Transfer Request.")
            selected_type_id = 101
            selected_type_label = "Internal Transfer Requests"

    print(f" -> Selected Submission Type: {selected_type_label} (ID: {selected_type_id})")

    # 2. Second Request: Save Form Data (Set Type and Business Unit)
    print("\n[2/3] Initializing submission configuration on server...")
    set_type_url = f"{host}/submissions/{submission_id}/save-form-data"
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
    print(" -> Success! Submission type and business unit initialized.")

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
    payload_file = os.path.join("submission-payloads", f"{selected_type_id}.json")
    print(f"\n[3/3] Preparing form data payload (Type ID: {selected_type_id})...")
    
    if os.path.exists(payload_file):
        print(f" -> Found specific payload file: '{payload_file}'")
        try:
            with open(payload_file, 'r') as f:
                submission_data = json.load(f)
            print(f" -> Successfully loaded payload from '{payload_file}'")
        except json.JSONDecodeError as e:
            print(f"\nError: Failed to parse JSON from payload file '{payload_file}': {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\nError reading payload file '{payload_file}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f" -> No payload file found at '{payload_file}'. Falling back to simple payload with title only.")
        submission_data = {}

    # Override/set the title
    submission_data['title'] = submission_title

    print(" -> Submitting updated form data payload...")
    save_url = f"{host}/submissions/{submission_id}/save-form-data"
    make_request(save_url, data_dict=submission_data)
    print(" -> Success! Submission details saved.")

    # Complete Message
    print("\nSubmission is created.")
    print(f"{host}/#/submissions/{submission_id}")
    print_app_footer(username)

if __name__ == '__main__':
    main()
