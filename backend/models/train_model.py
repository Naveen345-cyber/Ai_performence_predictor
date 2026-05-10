"""
NAV-AI Pro — Advanced Ensemble ML Model Trainer
Replaces simple LinearRegression with a VotingRegressor ensemble
(Random Forest + Gradient Boosting + Ridge Regression).
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score
import pickle
import os

# =====================================================
# 1. SYNTHETIC TRAINING DATA (50+ realistic samples)
# =====================================================
# Columns: attendance, mst_marks, study_hours, distraction_level (0-3), target_sgpa
np.random.seed(42)

def generate_training_data(n=100):
    """Generate realistic synthetic student performance data."""
    data = []
    for _ in range(n):
        att = np.random.uniform(40, 100)
        mst = np.random.uniform(30, 100)
        study = np.random.uniform(0, 12)
        distraction = np.random.choice([0, 1, 2, 3])  # None, Low, Medium, High
        
        # Realistic SGPA generation based on features
        base_sgpa = (
            (att * 0.025) +           # Attendance contributes ~2.5 points max
            (mst * 0.045) +            # MST contributes ~4.5 points max
            (study * 0.2) +            # Study hours contribute ~2.4 points max
            np.random.normal(0, 0.3)   # Noise
        )
        
        # Apply distraction penalty
        penalties = {0: 0, 1: 0.15, 2: 0.5, 3: 1.2}
        base_sgpa -= penalties[distraction]
        
        # Clamp to valid SGPA range
        sgpa = round(max(2.0, min(10.0, base_sgpa)), 2)
        
        data.append([att, mst, study, distraction, sgpa])
    
    return pd.DataFrame(data, columns=['attendance', 'mst_marks', 'study_hours', 'distraction', 'target_sgpa'])


def train_ensemble_model():
    """Train and save the ensemble predictor."""
    df = generate_training_data(150)
    
    X = df[['attendance', 'mst_marks', 'study_hours', 'distraction']]
    y = df['target_sgpa']
    
    # --- BUILD ENSEMBLE ---
    estimators = [
        ('rf', RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)),
        ('gb', GradientBoostingRegressor(n_estimators=80, max_depth=4, learning_rate=0.1, random_state=42)),
        ('ridge', Ridge(alpha=1.0))
    ]
    
    ensemble = VotingRegressor(estimators=estimators)
    ensemble.fit(X, y)
    
    # --- CROSS-VALIDATION SCORE ---
    scores = cross_val_score(ensemble, X, y, cv=5, scoring='r2')
    print(f"[SCORE] Ensemble R2 Score: {scores.mean():.4f} (+/- {scores.std():.4f})")
    
    # --- SAVE MODEL ---
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, 'ensemble_predictor.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(ensemble, f)
    
    # Also save the feature metadata for reference
    meta = {
        'features': ['attendance', 'mst_marks', 'study_hours', 'distraction'],
        'distraction_map': {'None': 0, 'Low': 1, 'Medium': 2, 'High': 3},
        'r2_score': round(scores.mean(), 4),
        'training_samples': len(df)
    }
    meta_path = os.path.join(model_dir, 'model_meta.pkl')
    with open(meta_path, 'wb') as f:
        pickle.dump(meta, f)
    
    print(f"[OK] Ensemble model saved to {model_path}")
    print(f"   Trained on {len(df)} samples with {len(estimators)} sub-models.")
    return ensemble


if __name__ == "__main__":
    train_ensemble_model()