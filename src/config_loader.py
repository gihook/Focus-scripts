#!/usr/bin/env python3
import os
import sys
import json

CONFIG_FILE = ".config.json"

def load_config(config_file=CONFIG_FILE):
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' is missing.", file=sys.stderr)
        print(f"Please copy '.config.example.json' to '{config_file}' and fill in your COOKIE and HOST.", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error: Failed to read or parse '{config_file}': {e}", file=sys.stderr)
        sys.exit(1)
        
    host = config.get("HOST")
    if not host:
        print(f"Error: 'HOST' must be set in '{config_file}'.", file=sys.stderr)
        sys.exit(1)
        
    users = config.get("USERS", [])
    if not users:
        cookie = config.get("COOKIE")
        if cookie:
            users = [{"USERNAME": "Default", "COOKIE": cookie}]
            
    if not users:
        print(f"Error: No valid cookies or users found in '{config_file}'. Please set 'COOKIE' or 'USERS'.", file=sys.stderr)
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

def print_user_header(username):
    banner = f"  ACTIVE USER SESSION: {username}  "
    border = "=" * len(banner)
    print("\n" + border)
    print(banner)
    print(border + "\n")
