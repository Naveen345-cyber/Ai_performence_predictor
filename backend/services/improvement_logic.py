def get_improvement_plan(attendance, study_hours, sleep_hours):
    suggestions = []
    
    if attendance < 75:
        suggestions.append("Critically low attendance. Priority: Attend all lectures next week to avoid 'detain' status.")
    
    if study_hours < 3:
        suggestions.append("Study hours are below average. Suggestion: Start with 2 'Pomodoro' sessions (25 min study / 5 min break).")
        
    if sleep_hours < 6:
        suggestions.append("Sleep deprivation detected. This kills focus. Try to hit 7 hours to improve memory retention.")
        
    if not suggestions:
        suggestions.append("You are in a great flow! Focus on advanced DSA (Graphs/DP) to stay ahead.")
        
    return suggestions