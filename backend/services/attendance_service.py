"""
NAV-AI Pro — Attendance Burn-Down Calculator
Implements the CGC 75% minimum attendance rule logic.
"""

def calculate_burndown(total_lectures, attended_lectures, upcoming_lectures=30):
    """
    Calculate attendance burn-down metrics for the CGC 75% rule.
    
    Returns a dict with:
        - current_pct: Current attendance percentage
        - status: 'safe' | 'warning' | 'danger'
        - can_bunk: How many more lectures you can skip and still have 75%
        - must_attend: How many consecutive lectures to attend to recover to 75%
        - projected_pct: Projected % if you attend all upcoming lectures
        - recovery_possible: Whether recovery is mathematically possible
    """
    if total_lectures == 0:
        return {
            "current_pct": 0.0,
            "status": "danger",
            "can_bunk": 0,
            "must_attend": 0,
            "projected_pct": 0.0,
            "recovery_possible": True,
            "message": "No lectures recorded yet. Start tracking!"
        }
    
    current_pct = round((attended_lectures / total_lectures) * 100, 2)
    
    # --- HOW MANY CAN YOU BUNK? ---
    # After bunking X more: attended / (total + X) >= 0.75
    # attended >= 0.75 * (total + X)
    # X <= (attended / 0.75) - total
    can_bunk = max(0, int((attended_lectures / 0.75) - total_lectures))
    
    # --- HOW MANY MUST YOU ATTEND TO RECOVER? ---
    # (attended + Y) / (total + Y) >= 0.75
    # attended + Y >= 0.75 * total + 0.75 * Y
    # 0.25 * Y >= 0.75 * total - attended
    # Y >= (0.75 * total - attended) / 0.25
    deficit = (0.75 * total_lectures) - attended_lectures
    must_attend = max(0, int(-(-deficit // 0.25)))  # Ceiling division
    
    # Projected if you attend ALL upcoming
    projected_pct = round(((attended_lectures + upcoming_lectures) / (total_lectures + upcoming_lectures)) * 100, 2)
    
    # Can you even recover?
    recovery_possible = must_attend <= upcoming_lectures
    
    # Status classification
    if current_pct >= 85:
        status = "safe"
    elif current_pct >= 75:
        status = "warning"
    else:
        status = "danger"
    
    # Generate human-readable message
    if status == "safe":
        message = f"🟢 You're cruising at {current_pct}%! You can safely skip {can_bunk} more lectures."
    elif status == "warning":
        message = f"🟡 You're at {current_pct}% — right on the edge. Only {can_bunk} bunks left before danger zone!"
    else:
        if recovery_possible:
            message = f"🔴 DANGER! You're at {current_pct}%. You MUST attend the next {must_attend} lectures straight to recover to 75%."
        else:
            message = f"🔴 CRITICAL! At {current_pct}%, recovery to 75% needs {must_attend} lectures but only {upcoming_lectures} remain. Talk to your HOD."
    
    return {
        "current_pct": current_pct,
        "status": status,
        "can_bunk": can_bunk,
        "must_attend": must_attend,
        "projected_pct": projected_pct,
        "recovery_possible": recovery_possible,
        "message": message
    }


def get_burndown_timeline(total_lectures, attended_lectures, future_count=30):
    """
    Generate a timeline showing attendance % for each future scenario.
    Returns list of dicts for charting.
    """
    timeline = []
    for i in range(future_count + 1):
        # Scenario 1: Attend all
        attend_all_pct = round(((attended_lectures + i) / (total_lectures + i)) * 100, 2) if (total_lectures + i) > 0 else 0
        # Scenario 2: Skip all remaining
        skip_all_pct = round((attended_lectures / (total_lectures + i)) * 100, 2) if (total_lectures + i) > 0 else 0
        
        timeline.append({
            "lecture": i,
            "attend_all": attend_all_pct,
            "skip_all": skip_all_pct,
            "threshold": 75.0
        })
    return timeline
