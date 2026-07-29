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

def parse_arguments():
    parser = argparse.ArgumentParser(description="Log in to Rationaletech CHub and save session cookies.")
    parser.add_argument(
        '-e', '--email',
        type=str,
        help="Specify the email/username to log in with directly (skips the email prompt)"
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # 1. Load host from .config.json or use default
    host = "https://chub-dev.rationaletech.com"
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            host = config.get("HOST", host)
        except Exception as e:
            print(f"Warning: Failed to parse '{CONFIG_FILE}', using default host. Error: {e}", file=sys.stderr)
            
    # Remove any trailing slash from host for url construction
    host = host.rstrip('/')

    # 2. Get email from argument or prompt user
    email = args.email
    if not email:
        try:
            email = input("Enter your email for login: ").strip()
            if not email:
                print("Error: Email cannot be empty.", file=sys.stderr)
                sys.exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)

    print(f"\nInitiating login flow for user '{email}' against '{host}'...")

    # Set up cookie jar and HTTP opener
    cookie_jar = http.cookiejar.CookieJar()
    handler = urllib.request.HTTPCookieProcessor(cookie_jar)
    opener = urllib.request.build_opener(handler)

    # Step 1: Request the login-tenant endpoint to get the authorize URL
    print("[1/3] Contacting login gateway...")
    init_url = f"{host}/login-tenant"
    req1 = urllib.request.Request(init_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with opener.open(req1) as response1:
            authorize_url = response1.geturl()
    except Exception as e:
        print(f"Error: Failed to contact login gateway: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 2: POST credentials to the authorize URL
    print("[2/3] Simulating OIDC Authorization...")
    exp_timestamp = int(time.time()) + 7200  # 2 hours expiration
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
        print(f"Error during authorization: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse authorization code and state from HTML
    code_match = re.search(r'name="code"\s+value="([^"]+)"', html)
    state_match = re.search(r'name="state"\s+value="([^"]+)"', html)

    if not code_match or not state_match:
        # Check if the page is indicating user not found or error
        if "User Account Not Found" in html:
            print(f"\nError: User account '{email}' was not found in the CHub system database.", file=sys.stderr)
        else:
            print("\nError: Failed to parse OIDC code or state from authorize callback form.", file=sys.stderr)
        sys.exit(1)

    code = code_match.group(1)
    state = state_match.group(1)

    # Step 3: Send signin callback POST to signin-oidc
    print("[3/3] Authenticating session callback...")
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
            # Successfully authenticated!
            pass
    except urllib.error.HTTPError as e:
        print(f"\nError: Authentication callback failed with status {e.code}", file=sys.stderr)
        try:
            body = e.read().decode('utf-8')
            if "User Account Not Found" in body:
                print(f"Details: User account '{email}' not found.", file=sys.stderr)
            else:
                print(f"Response: {body[:300]}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)
    except Exception as e:
        print(f"\nError completing authentication callback: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Extract cookies and format Cookie header string
    cookie_parts = []
    host_domain = host.split("://")[-1].split(":")[0]  # get domain name, e.g. chub-dev.rationaletech.com
    
    for c in cookie_jar:
        # Check if cookie domain matches target host domain
        if host_domain in c.domain:
            cookie_parts.append(f"{c.name}={c.value}")

    if not cookie_parts:
        print("\nError: No authentication cookies were retrieved from the server response.", file=sys.stderr)
        sys.exit(1)

    cookie_string = "; ".join(cookie_parts)

    # 5. Load/Create .config.json and save user cookies
    users_list = config.get("USERS", [])
    
    # If the file had a flat cookie and we are converting to list, support it
    if not users_list:
        flat_cookie = config.get("COOKIE")
        if flat_cookie:
            users_list = [{"USERNAME": "Default", "COOKIE": flat_cookie}]

    # Update or insert user
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

    config["USERS"] = users_list
    config["HOST"] = host  # Ensure HOST is stored/retained

    # Clean up obsolete flat COOKIE key to keep the config clean
    if "COOKIE" in config:
        del config["COOKIE"]

    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\n-> Success! Successfully logged in as '{email}'.")
        print(f"-> Session saved in '{CONFIG_FILE}'.")
    except Exception as e:
        print(f"\nError: Failed to write configuration to '{CONFIG_FILE}': {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
