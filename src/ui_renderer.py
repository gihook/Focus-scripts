#!/usr/bin/env python3
import sys
import os

def clear_screen():
    if sys.stdout.isatty():
        os.system('cls' if os.name == 'nt' else 'clear')

def print_app_header(host=""):
    host_str = f" | Server: {host}" if host else ""
    header_text = f" CHub Console Application{host_str} "
    border = "=" * 80
    padding = (80 - len(header_text)) // 2
    header_line = "=" * padding + header_text + "=" * (80 - padding - len(header_text))
    # Print header using ANSI reverse video (inverted colors) and bold
    print(f"\033[7m\033[1m{header_line}\033[0m")

def print_app_footer(username):
    footer_text = f" Session User: {username} | Status: Active "
    border = "=" * 80
    padding = (80 - len(footer_text)) // 2
    footer_line = "=" * padding + footer_text + "=" * (80 - padding - len(footer_text))
    # Print footer using ANSI reverse video (inverted colors) and bold
    print(f"\033[7m\033[1m{footer_line}\033[0m")

def format_workflow_steps_ascii(steps):
    if not isinstance(steps, list) or not steps:
        return ""
        
    lines = ["\nWorkflow Pathway:"]
    for i, step in enumerate(steps):
        label = step.get('label', 'N/A')
        status = step.get('status', 'N/A')
        is_active = step.get('isActive', False)
        is_complete = step.get('isComplete', False)
        
        # Determine status display label
        if is_active:
            status_lbl = "ACTIVE"
            step_prefix = " ▶ "
        elif is_complete:
            status_lbl = "COMPLETE"
            step_prefix = "   "
        else:
            status_lbl = "PENDING"
            step_prefix = "   "
            
        # Get user full names
        users = step.get('users', [])
        user_names = [u.get('fullName') for u in users if u.get('fullName')]
        users_str = ", ".join(user_names) if user_names else "No users"
        
        # Build box/lines
        lines.append(f"{step_prefix}[Step {i+1}] {label} ({status_lbl})")
        lines.append(f"      Assigned: {users_str}")
        
        # Add arrow if not the last step
        if i < len(steps) - 1:
            lines.append("           ↓")
            
    return "\n".join(lines)
