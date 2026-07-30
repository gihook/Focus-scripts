#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import http.cookiejar
import re

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
        
    return host, users, config

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
        
    print("Available Users to perform search:")
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

def print_details_card(details, label="SUBMISSION DETAILS"):
    print("\n" + "="*50)
    print(f"{label} (Display ID: {details.get('displayId', 'N/A')})")
    print("="*50)
    print(f"UUID:            {details.get('id', 'N/A')}")
    title_val = details.get('title', details.get('subject', 'No Title'))
    print(f"Title/Subject:   {title_val}")
    print(f"Status:          {details.get('status', 'N/A')}")
    print(f"Created:         {details.get('creationTimestamp', 'N/A')}")
    
    # Workflow information
    workflow = details.get('workflow', {})
    if workflow:
        print(f"Workflow Status: {workflow.get('status', 'N/A')}")
        steps = workflow.get('steps', [])
        active_steps = [s for s in steps if s.get('isActive')]
        if active_steps:
            print("\nActive Steps:")
            for idx, step in enumerate(active_steps, 1):
                s_status = step.get('label', step.get('status', 'N/A'))
                s_type = step.get('stepType', 'N/A')
                print(f"  - Step #{idx}: Status={s_status} (Type={s_type})")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Search and view submissions on Rationaletech CHub.")
    parser.add_argument(
        '-u', '--user',
        type=str,
        help="Specify the USERNAME to use for searching (skips the user selection prompt)"
    )
    parser.add_argument(
        '-p', '--page',
        type=int,
        default=1,
        help="Initial page number to load (default: 1)"
    )
    parser.add_argument(
        '-q', '--query',
        type=str,
        help="Initial search term/filter for submissions"
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Load configuration
    host, users, config = load_config()

    # Prompt user to select which account to search with
    username, cookie = select_user(users, args.user)
    print(f"-> Selected Search Requester Account: {username}\n")

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

    def make_get_request(url):
        req = urllib.request.Request(url, headers=headers, method='GET')
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print(f"Error: HTTP Search Request failed with status {e.code}", file=sys.stderr)
            try:
                print(f"Response Body: {e.read().decode('utf-8')}", file=sys.stderr)
            except Exception:
                pass
            sys.exit(1)
        except Exception as e:
            print(f"Error connecting to server search endpoint: {e}", file=sys.stderr)
            sys.exit(1)

    def make_post_request(url, data_dict=None):
        payload = json.dumps(data_dict).encode('utf-8') if data_dict is not None else b'{}'
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print(f"Error: HTTP POST request failed with status {e.code}", file=sys.stderr)
            try:
                print(f"Response Body: {e.read().decode('utf-8')}", file=sys.stderr)
            except Exception:
                pass
            sys.exit(1)
        except Exception as e:
            print(f"Error executing POST request: {e}", file=sys.stderr)
            sys.exit(1)

    page = args.page
    search_term = args.query if args.query is not None else ""
    should_fetch = True
    items = []
    
    while True:
        term_desc = f" matching '{search_term}'" if search_term else ""
        if should_fetch:
            print(f"Fetching submissions page {page}{term_desc} from server...")
            
            search_url = f"{host}/submissions/search?pageNumber={page}&pageSize=10"
            if search_term:
                search_url += f"&searchTerm={urllib.parse.quote(search_term)}"
                
            res_data = make_get_request(search_url)

            # Extract items
            items = []
            if isinstance(res_data, list):
                items = res_data
            elif isinstance(res_data, dict):
                items = res_data.get('items', res_data.get('results', res_data.get('data', [])))
                if not items:
                    # Fallback check
                    for val in res_data.values():
                        if isinstance(val, list) and all(isinstance(x, dict) for x in val):
                            items = val
                            break

            if not items:
                print(f"\nNo submissions found on Page {page}{term_desc}.")
                if page > 1:
                    print("Returning to previous page...")
                    page -= 1
                    time.sleep(1)
                    should_fetch = True
                    continue
                else:
                    # If they filter and get no results on page 1, let them clear or change filter
                    if search_term:
                        print("\nYou can clear the search filter using 'c' or enter a new one.")
                        items = []
                    else:
                        print("Exiting.")
                        sys.exit(0)

        # Display submissions table
        print(f"\n--- Submissions (Page {page}){term_desc if search_term else ''} ---")
        for index, item in enumerate(items, 1):
            display_id = item.get('displayId', 'N/A')
            title = item.get('title', item.get('subject', 'No Title'))
            status = item.get('status', 'N/A')
            print(f"  [{index}] ID: {display_id:<8} - {title:<45} (Status: {status})")

        print("\nNavigation / Filter Options:")
        options_text = []
        if page > 1:
            options_text.append("'p' for previous page")
        options_text.append("'n' for next page")
        options_text.append("'f <query>' to filter list")
        options_text.append("'<number>' to view details")
        if search_term:
            options_text.append("'c' to clear filter")
        options_text.append("'q' to quit")
        print("  " + " | ".join(options_text))

        try:
            choice = input("\nEnter choice: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

        if not choice:
            should_fetch = False
            continue

        choice_lower = choice.lower().strip()

        # Check if choice is a valid number to view details
        try:
            idx = int(choice_lower) - 1
            if 0 <= idx < len(items):
                selected_item = items[idx]
                submission_uuid = selected_item.get('id')
                if not submission_uuid:
                    print("Error: Could not retrieve submission UUID.")
                    time.sleep(1.5)
                    should_fetch = False
                    continue
                
                # Fetch full details
                print(f"\nFetching full details for submission {selected_item.get('displayId', 'N/A')}...")
                detail_url = f"{host}/submissions/{submission_uuid}"
                details = make_get_request(detail_url)
                
                # Print details cleanly
                print_details_card(details)
                
                # Extract and list available actions
                while True:
                    actions = details.get('availableActions', [])
                    print("\nAvailable Actions:")
                    if actions:
                        for idx_act, act in enumerate(actions, 1):
                            action_id = act.get('actionId', 'N/A')
                            is_disabled = act.get('isDisabled', False)
                            status_str = " (Disabled)" if is_disabled else ""
                            print(f"  [{idx_act}] {action_id}{status_str}")
                    else:
                        print("  - None")
                    print("="*50)
                    
                    try:
                        act_choice = input("\nSelect an action number to execute (or press Enter to return): ").strip()
                    except (KeyboardInterrupt, EOFError):
                        break

                    if not act_choice:
                        break

                    try:
                        act_idx = int(act_choice) - 1
                        if 0 <= act_idx < len(actions):
                            selected_act = actions[act_idx]
                            action_id = selected_act.get('actionId', 'N/A')
                            
                            if selected_act.get('isDisabled', False):
                                print(f"Error: Action '{action_id}' is currently disabled.")
                                time.sleep(1.5)
                                continue
                                
                            form_provider_url = selected_act.get('formProviderUrl')
                            if not form_provider_url:
                                print(f"Error: No form provider URL specified for action '{action_id}'.")
                                time.sleep(1.5)
                                continue
                                
                            # Resolve form provider URL
                            if form_provider_url.startswith('/'):
                                action_info_url = f"{host}{form_provider_url}"
                            else:
                                action_info_url = f"{host}/{form_provider_url}"
                                
                            print(f"\nFetching action details for '{action_id}'...")
                            action_details = make_get_request(action_info_url)
                            
                            action_post_url = action_details.get('url', '')
                            if not action_post_url:
                                print(f"Error: Action provider response did not return a submit URL.")
                                time.sleep(1.5)
                                continue
                                
                            if not action_post_url.startswith('/'):
                                action_post_url = '/' + action_post_url
                            full_post_url = f"{host}{action_post_url}"
                            
                            # Parse fields and prompt user
                            form_fields = action_details.get('formFields', [])
                            post_payload = {}
                            
                            print(f"\nExecuting '{action_id}' Action Form:")
                            for field in form_fields:
                                key = field.get('key', field.get('name'))
                                if not key:
                                    continue
                                field_type = field.get('type', '')
                                
                                if field_type == 'textarea':
                                    label = field.get('props', {}).get('label', field.get('label', key))
                                    try:
                                        val = input(f"  Enter {label}: ").strip()
                                    except (KeyboardInterrupt, EOFError):
                                        print("\nAction cancelled.")
                                        break
                                    post_payload[key] = val
                                else:
                                    post_payload[key] = field.get('value', '')
                            else:
                                # Send action execute POST
                                print(" -> Submitting action execution request...")
                                make_post_request(full_post_url, data_dict=post_payload)
                                print(f" -> Success! Action '{action_id}' executed.")
                                time.sleep(1.5)
                                
                                # Refresh details from server
                                print("\nRefreshing submission details...")
                                details = make_get_request(detail_url)
                                
                                # Print refreshed details cleanly
                                print_details_card(details)
                                continue
                        else:
                            print(f"Number out of range. Please enter an action number between 1 and {len(actions)}.")
                            time.sleep(1.5)
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
                        time.sleep(1.5)
                
                print()
                should_fetch = False
                continue
            else:
                print(f"Number out of range. Please enter a number between 1 and {len(items)}.")
                time.sleep(1.5)
                print()
                should_fetch = False
                continue
        except ValueError:
            # Not a number, fallback to command choices
            pass

        if choice_lower == 'q':
            print("Exiting.")
            sys.exit(0)

        elif choice_lower == 'p' and page > 1:
            page -= 1
            should_fetch = True
            print()
            continue

        elif choice_lower == 'n':
            page += 1
            should_fetch = True
            print()
            continue

        elif choice_lower == 'c':
            search_term = ""
            page = 1
            should_fetch = True
            print()
            continue

        elif choice_lower.startswith('f '):
            search_term = choice[2:].strip()
            page = 1
            should_fetch = True
            print()
            continue

        else:
            print("Invalid command.")
            time.sleep(1.5)
            should_fetch = False
            print()

if __name__ == '__main__':
    main()
