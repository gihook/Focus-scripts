#!/usr/bin/env python3

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
