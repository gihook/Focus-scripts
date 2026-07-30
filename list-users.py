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

from lib.utils import select_user

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

def extract_xsrf_token(cookie_str):
    parts = cookie_str.split(';')
    for part in parts:
        part = part.strip()
        if part.startswith('XSRF-TOKEN='):
            return part[len('XSRF-TOKEN='):]
    return 'CfDJ8B3cU1ZsNd1MirISpSbNJd9xEGENsXFsuDl7V5fCVCB8-pA-dO7yChyFNS8TfS_q_-Gz5K5WJeKA4q_0zrp2HZ0xaXWgMy2fIYPUWiVK851Gk2rDAn-zV9tVPYhlouwMrtmtQPeeP9L-8KxFeDtsLPVuevjpLwWrJjvto0piDPQUVGlit2-AOQK2ByM-LOAYHQ'

def parse_arguments():
    parser = argparse.ArgumentParser(description="Search and view users on Rationaletech CHub.")
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
    return parser.parse_args()

def login_user(host, email, config):
    print(f" -> Initiating login flow for user '{email}' against '{host}'...")
    cookie_jar = http.cookiejar.CookieJar()
    handler = urllib.request.HTTPCookieProcessor(cookie_jar)
    opener = urllib.request.build_opener(handler)

    # Step 1: Contact gateway
    init_url = f"{host}/login-tenant"
    req1 = urllib.request.Request(init_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with opener.open(req1) as response1:
            authorize_url = response1.geturl()
    except Exception as e:
        print(f"    Error contacting login gateway: {e}", file=sys.stderr)
        return False

    # Step 2: Post OIDC credentials
    exp_timestamp = int(time.time()) + 7200
    post_data = {
        'username': email,
        'claims': json.dumps({'email': email, 'exp': exp_timestamp})
    }
    payload = urllib.parse.urlencode(post_data).encode('utf-8')
    req2 = urllib.request.Request(
        authorize_url, 
        data=payload, 
        headers={
            'User-Agent': 'Mozilla/5.0', 
            'Content-Type': 'application/x-www-form-urlencoded'
        }, 
        method='POST'
    )
    try:
        with opener.open(req2) as response2:
            html = response2.read().decode('utf-8')
    except Exception as e:
        print(f"    Error during authorization: {e}", file=sys.stderr)
        return False

    code_match = re.search(r'name="code"\s+value="([^"]+)"', html)
    state_match = re.search(r'name="state"\s+value="([^"]+)"', html)

    if not code_match or not state_match:
        if "User Account Not Found" in html:
            print(f"    Error: User account '{email}' was not found in the server database.", file=sys.stderr)
        else:
            print("    Error: Failed to parse OIDC credentials from callback form.", file=sys.stderr)
        return False

    code = code_match.group(1)
    state = state_match.group(1)

    # Step 3: Callback signin-oidc
    callback_url = f"{host}/signin-oidc"
    cb_data = {
        'code': code,
        'state': state
    }
    cb_payload = urllib.parse.urlencode(cb_data).encode('utf-8')
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://oauth-mock.rationaletech.com',
        'Referer': 'https://oauth-mock.rationaletech.com/'
    }
    req3 = urllib.request.Request(callback_url, data=cb_payload, headers=headers, method='POST')
    try:
        with opener.open(req3) as response3:
            pass
    except Exception as e:
        print(f"    Error completing OIDC session callback: {e}", file=sys.stderr)
        return False

    # Extract cookies
    cookie_parts = []
    host_domain = host.split("://")[-1].split(":")[0]
    for c in cookie_jar:
        if host_domain in c.domain:
            cookie_parts.append(f"{c.name}={c.value}")

    if not cookie_parts:
        print("    Error: No authentication cookies retrieved from response headers.", file=sys.stderr)
        return False

    cookie_string = "; ".join(cookie_parts)

    # Save to config object
    users_list = config.setdefault("USERS", [])
    
    # Handle backward-compatibility flat COOKIE migration if needed
    if not users_list and "COOKIE" in config:
        users_list.append({"USERNAME": "Default", "COOKIE": config["COOKIE"]})
        del config["COOKIE"]

    user_updated = False
    for u in users_list:
        if u.get("USERNAME", "").lower() == email.lower():
            u["COOKIE"] = cookie_string
            u["USERNAME"] = email  # preserve original casing
            user_updated = True
            break

    if not user_updated:
        users_list.append({
            "USERNAME": email,
            "COOKIE": cookie_string
        })

    return True

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

    page = args.page
    
    while True:
        print(f"Fetching users page {page} from server...")
        search_url = f"{host}/Users/search?pageNumber={page}&pageSize=10"
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
            print(f"\nNo users found on Page {page}.")
            if page > 1:
                print("Returning to previous page...")
                page -= 1
                time.sleep(1)
                continue
            else:
                print("Exiting.")
                sys.exit(0)

        # Display user table
        print(f"\n--- System Users (Page {page}) ---")
        for index, item in enumerate(items, 1):
            email = item.get('email', 'N/A')
            full_name = item.get('fullName', f"{item.get('firstName', '')} {item.get('lastName', '')}".strip() or 'N/A')
            designation = item.get('designation', 'N/A')
            print(f"  [{index}] {full_name:<25} - {email:<35} ({designation})")

        print("\nNavigation / Selection Options:")
        options_text = []
        if page > 1:
            options_text.append("'p' for previous page")
        options_text.append("'n' for next page")
        options_text.append("'s <indices>' to log in selected user(s) (e.g. s 1, 3)")
        options_text.append("'q' to quit")
        print("  " + " | ".join(options_text))

        try:
            choice = input("\nEnter choice: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

        if not choice:
            continue

        if choice == 'q':
            print("Exiting.")
            sys.exit(0)

        elif choice == 'p' and page > 1:
            page -= 1
            print()
            continue

        elif choice == 'n':
            page += 1
            print()
            continue

        elif choice.startswith('s '):
            raw_selection = choice[2:].strip()
            if not raw_selection:
                print("Error: No indices specified after 's'.")
                time.sleep(1.5)
                continue

            # Parse selections robustly
            parts = raw_selection.replace(',', ' ').split()
            selected_indices = []
            for part in parts:
                try:
                    idx = int(part) - 1
                    if 0 <= idx < len(items):
                        selected_indices.append(idx)
                    else:
                        print(f"Index {part} is out of range.")
                except ValueError:
                    print(f"Invalid index format: '{part}'")

            if not selected_indices:
                time.sleep(1.5)
                continue

            # Execute OIDC log-ins
            success_count = 0
            for idx in selected_indices:
                user_item = items[idx]
                user_email = user_item.get('email')
                if not user_email:
                    print(f" -> Skipping user at index {idx+1}: email property is missing.")
                    continue
                
                success = login_user(host, user_email, config)
                if success:
                    success_count += 1
                    print(f" -> Success! Logged in as '{user_email}'.")
                else:
                    print(f" -> Failed to log in as '{user_email}'.")

            # Write updated config to .config.json if at least one user logged in successfully
            if success_count > 0:
                try:
                    with open(CONFIG_FILE, 'w') as f:
                        json.dump(config, f, indent=2)
                    print(f"\n-> Success! Successfully logged in {success_count} user(s). Config file updated.")
                except Exception as e:
                    print(f"\nError writing to '{CONFIG_FILE}': {e}", file=sys.stderr)
            
            time.sleep(2)
            print()
            continue

        else:
            print("Invalid command.")
            time.sleep(1.5)
            print()

if __name__ == '__main__':
    main()
