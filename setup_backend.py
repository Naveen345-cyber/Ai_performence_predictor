"""
NAV-AI Pro — Backend Setup Script (Phase 2)
Initializes database tables and trains the ensemble ML model.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.api.database_helper import init_db
from backend.models.train_model import train_ensemble_model


def init_project():
    # 1. Create Folders
    for folder in ['database', 'backend/models', 'frontend/assets', 'frontend/components']:
        os.makedirs(folder, exist_ok=True)

    # 2. Initialize Database
    print("[DB] Initializing database...")
    init_db()

    # 3. Train Ensemble AI Model
    print("[ML] Training ensemble ML model...")
    train_ensemble_model()

    print("\n[OK] NAV-AI Pro Phase 2 initialized successfully!")
    print("   Run with: streamlit run frontend/app.py")


if __name__ == "__main__":
    init_project()