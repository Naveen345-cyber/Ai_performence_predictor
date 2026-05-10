"""NAV-AI Pro — Flask API Server. Serves frontend + REST API."""
from flask import Flask, jsonify, request, send_from_directory, send_file
import sys, os, tempfile, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.api.database_helper import (
    init_db, get_or_create_student, save_semester_history, load_semester_history,
    save_prediction, get_prediction_history, save_attendance, load_attendance,
    save_ai_report, get_latest_report, get_all_reports, update_student_rank,
    save_assessment, save_assessment_questions, get_understanding_baseline,
    update_understanding_baseline, get_assessment_history, get_subject_understanding_summary
)
from backend.services.profile_service import calculate_weighted_sgpa, get_grade_prediction, get_performance_tier
from backend.services.attendance_service import calculate_burndown, get_burndown_timeline
from backend.services.chatbot_service import get_ai_response
from backend.services.pdf_service import generate_academic_report
from backend.services.understanding_service import (
    generate_quiz_questions, calculate_understanding_index, get_understanding_insights
)
from backend.constants import ALL_SUBJECTS, CGC_CSE_SUBJECTS

app = Flask(__name__, static_folder='frontend', static_url_path='')

# --- ERROR HANDLER ---
@app.errorhandler(Exception)
def handle_error(e):
    traceback.print_exc()
    return jsonify(error=str(e)), 500

# --- STATIC FILES ---
@app.route('/')
def serve_index():
    return send_from_directory('frontend', 'index.html')

@app.route('/css/<path:f>')
def serve_css(f):
    return send_from_directory('frontend/css', f)

@app.route('/js/<path:f>')
def serve_js(f):
    return send_from_directory('frontend/js', f)

# --- API: HEALTH ---
@app.route('/api/health')
def api_health():
    return jsonify(status='ok', version='2.0')

# --- API: STUDENT ---
@app.route('/api/student/<name>')
def api_student(name):
    s = get_or_create_student(name)
    h = load_semester_history(name)
    cgpa = calculate_weighted_sgpa(h)
    tier, color = get_performance_tier(cgpa) if cgpa > 0 else ("--", "#888")
    return jsonify(student=s, history=h, cgpa=cgpa, tier=tier, color=color)

# --- API: SEMESTER HISTORY ---
@app.route('/api/history/<name>', methods=['POST'])
def api_save_history(name):
    save_semester_history(name, request.json['history'])
    return jsonify(success=True)

# --- API: PREDICT ---
@app.route('/api/predict', methods=['POST'])
def api_predict():
    d = request.json
    pred = get_grade_prediction(d['att'], d['mst'], d['study'], d['distraction'])
    tier, color = get_performance_tier(pred)
    save_prediction(d['name'], d['att'], d['mst'], d['study'], d['distraction'], pred)
    h = load_semester_history(d['name'])
    return jsonify(predicted=pred, tier=tier, color=color, history=h)

@app.route('/api/predictions/<name>')
def api_pred_history(name):
    return jsonify(get_prediction_history(name, 10))

# --- API: ATTENDANCE ---
@app.route('/api/attendance/<name>')
def api_get_att(name):
    return jsonify(load_attendance(name))

@app.route('/api/attendance/<name>', methods=['POST'])
def api_save_att(name):
    d = request.json
    save_attendance(name, d['total'], d['attended'])
    r = calculate_burndown(d['total'], d['attended'], d.get('upcoming', 30))
    t = get_burndown_timeline(d['total'], d['attended'], d.get('upcoming', 30))
    return jsonify(burndown=r, timeline=t)

# --- API: SUBJECTS ---
@app.route('/api/subjects')
def api_subjects():
    return jsonify(all=ALL_SUBJECTS, by_semester=CGC_CSE_SUBJECTS)

# --- API: AI REPORT ---
@app.route('/api/ai-report', methods=['POST'])
def api_ai_report():
    d = request.json
    q = f"I am a 4th Sem CSE student at CGC Mohali. Create a detailed study plan for {d['subject']} focusing on {d['topic']}. Include: 1) Key concepts 2) Practice problems 3) Time allocation 4) Resources."
    ctx = f"Student: {d['name']}, Target: 9.2, Subject: {d['subject']}"
    advice = get_ai_response(q, ctx)
    save_ai_report(d['name'], d['subject'], d['topic'], advice)
    return jsonify(report=advice)

@app.route('/api/reports/<name>')
def api_reports(name):
    return jsonify(get_all_reports(name, 20))

# --- API: PDF DOWNLOAD ---
@app.route('/api/pdf/<name>')
def api_pdf(name):
    h = load_semester_history(name)
    preds = get_prediction_history(name, 1)
    pd_ = preds[0] if preds else None
    rpt = get_latest_report(name)
    ai = rpt.get('report_content', '') if rpt else None
    pdf = generate_academic_report(name, h, prediction_data=pd_, ai_report_text=ai)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp.write(pdf)
    tmp.close()
    return send_file(tmp.name, as_attachment=True, download_name=f'NAV_AI_Report_{name}.pdf', mimetype='application/pdf')

# --- API: UNDERSTANDING LEVEL ASSESSMENT ---
@app.route('/api/understanding/quiz', methods=['POST'])
def api_generate_quiz():
    d = request.json
    questions = generate_quiz_questions(
        d['subject'], d['topic'],
        difficulty=d.get('difficulty', 'medium'),
        count=d.get('count', 5)
    )
    return jsonify(questions=questions)

@app.route('/api/understanding/submit', methods=['POST'])
def api_submit_assessment():
    d = request.json
    name = d['name']
    subject = d['subject']
    topic = d['topic']
    difficulty = d.get('difficulty', 'medium')
    questions = d['questions']  # list of question results
    time_taken = d['time_taken_seconds']

    total = len(questions)
    correct = sum(1 for q in questions if q.get('is_correct'))

    # Get student's personal baseline for fair comparison
    baseline = get_understanding_baseline(name, subject)
    baseline_time = baseline['avg_time_per_question']

    # Calculate NLE Understanding Index
    result = calculate_understanding_index(
        correct, total, time_taken, baseline_time, difficulty
    )

    # Save assessment
    assessment_id = save_assessment(
        name, subject, topic, difficulty, total, correct,
        time_taken, result['comprehension_score'],
        result['speed_ratio'], result['understanding_index'], result['tier']
    )

    # Save individual question results
    save_assessment_questions(assessment_id, questions)

    # Update student's personal baseline (self-normalized)
    update_understanding_baseline(
        name, subject, result['avg_time_per_q'], correct / total if total > 0 else 0
    )

    # Get insights
    insights = get_understanding_insights(result, subject, topic)

    return jsonify(
        assessment_id=assessment_id,
        result=result,
        insights=insights,
        baseline=baseline
    )

@app.route('/api/understanding/history/<name>')
def api_understanding_history(name):
    history = get_assessment_history(name, 20)
    summary = get_subject_understanding_summary(name)
    return jsonify(history=history, summary=summary)

init_db()

if __name__ == '__main__':
    print("[NAV-AI Pro] Starting server at http://localhost:5000")
    app.run(debug=True, port=5000, use_reloader=True, reloader_type='stat',
            exclude_patterns=['**/site-packages/**'])
