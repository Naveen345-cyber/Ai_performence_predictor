"""
NAV-AI Pro — Profile Service
SGPA calculation and ML-powered grade forecasting.
Now uses the ensemble model when available, with formula fallback.
"""
import pickle
import os
import numpy as np
import pandas as pd


def calculate_weighted_sgpa(history):
    """Calculates average SGPA from the stored history dictionary."""
    if not history:
        return 0.0
    valid_scores = [float(s) for s in history.values() if s > 0]
    return round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0.0


def get_grade_prediction(att, mst, study_h, distraction):
    """
    Professional prediction logic.
    Uses ensemble ML model if available, falls back to weighted formula.
    """
    distraction_map = {"None": 0, "Low": 1, "Medium": 2, "High": 3}
    distraction_val = distraction_map.get(distraction, 0)
    
    # Try loading the ensemble model
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               '..', 'models', 'ensemble_predictor.pkl')
    
    if os.path.exists(model_path):
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            # Use DataFrame with proper feature names to match training data
            features = pd.DataFrame([[att, mst, study_h, distraction_val]],
                                    columns=['attendance', 'mst_marks', 'study_hours', 'distraction'])
            prediction = model.predict(features)[0]
            # Clamp to valid range
            return round(max(2.0, min(10.0, prediction)), 2)
        except Exception:
            pass  # Fall through to formula
    
    # Fallback: Original weighted formula with distraction penalty
    penalties = {"None": 0, "Low": 0.1, "Medium": 0.4, "High": 0.9}
    base = (mst * 0.5) + (att * 0.3) + (study_h * 2)
    return round((base / 12) - penalties.get(distraction, 0), 2)


def get_performance_tier(sgpa):
    """Classify SGPA into performance tiers."""
    if sgpa >= 9.0:
        return "🏆 Outstanding", "#00ff88"
    elif sgpa >= 8.0:
        return "⭐ Excellent", "#00d2ff"
    elif sgpa >= 7.0:
        return "✅ Good", "#ffd700"
    elif sgpa >= 6.0:
        return "⚠️ Average", "#ff8c00"
    else:
        return "🚨 At Risk", "#ff4444"