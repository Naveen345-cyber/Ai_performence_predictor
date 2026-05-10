import os

# Define the structure
folders = [
    "backend/api",
    "backend/models",
    "backend/services",
    "frontend/assets",
    "frontend/components",
    "frontend/styles",
    "database"
]

files = {
    "backend/api/main.py": "# FastAPI/Flask entry point\nprint('Backend API running...')",
    "backend/models/train_model.py": "# Script to train your AI model\n# We will add Scikit-learn code here later",
    "backend/services/chatbot_service.py": "# AI Chatbot Logic\n# Connect to OpenAI or Groq here",
    "backend/services/scheduler.py": "# Logic for generating study schedules",
    "frontend/app.py": "import streamlit as st\n\nst.set_page_config(page_title='AI Student Hub', layout='wide')\nst.title('AI Student Performance Predictor 🚀')\nst.write('Welcome to your GenZ Study Dashboard!')",
    "frontend/styles/theme.css": "/* 3D Glassmorphism Theme */\n[data-testid='stAppViewContainer'] {\n    background: #0f0c29;\n}",
    "database/schema.sql": "-- SQL commands to create your tables\nCREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT, attendance REAL);",
    ".env": "API_KEY=your_key_here\nDATABASE_URL=database/students.db",
    "README.md": "# Student AI Predictor Project\n4th Semester Internal Exam Project."
}

def create_project():
    # Create Folders
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"Created folder: {folder}")

    # Create Files
    for path, content in files.items():
        # The 'encoding="utf-8"' below is what fixes the error!
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created file: {path}")

    print("\n✅ Project structure is ready! Open this folder in VS Code.")

if __name__ == "__main__":
    create_project()