import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os, sys, tempfile

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from backend.constants import ALL_SUBJECTS, CGC_CSE_SUBJECTS
from backend.services.profile_service import calculate_weighted_sgpa, get_grade_prediction, get_performance_tier
from backend.services.chatbot_service import get_ai_response
from backend.services.attendance_service import calculate_burndown, get_burndown_timeline
from backend.services.pdf_service import generate_academic_report
from backend.api.database_helper import (
    init_db, get_or_create_student, save_semester_history, load_semester_history,
    save_prediction, get_prediction_history, save_attendance, load_attendance,
    save_ai_report, get_latest_report, update_student_rank
)

# --- PAGE CONFIG ---
st.set_page_config(page_title="NAV-AI Pro ERP", page_icon="🎓", layout="wide")

# --- LOAD CSS ---
css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'styles', 'theme.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- INIT DB ---
init_db()

# --- SESSION STATE ---
if 'user_name' not in st.session_state:
    st.session_state.user_name = "Naveen"
if 'last_prediction' not in st.session_state:
    st.session_state.last_prediction = None
if 'last_ai_report' not in st.session_state:
    st.session_state.last_ai_report = None

# --- SIDEBAR PROFILE ---
st.sidebar.markdown("""
<div style="text-align:center; padding:10px;">
    <div style="width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,#6a11cb,#2575fc);
    margin:0 auto 10px;display:flex;align-items:center;justify-content:center;font-size:36px;
    box-shadow:0 4px 20px rgba(106,17,203,0.4);">🎓</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("NAV-AI Pro")
st.session_state.user_name = st.sidebar.text_input("Student Name", st.session_state.user_name)
student = get_or_create_student(st.session_state.user_name)

# Load persistent history for sidebar CGPA
history = load_semester_history(st.session_state.user_name)
cgpa = calculate_weighted_sgpa(history)
tier_label, tier_color = get_performance_tier(cgpa) if cgpa > 0 else ("—", "#888")

st.sidebar.markdown(f"""
<div class="glass-card" style="text-align:center;margin-top:10px;">
    <div style="font-size:28px;font-weight:800;color:{tier_color};">{cgpa}</div>
    <div style="color:#aaa;font-size:12px;">CGPA • {tier_label}</div>
    <hr style="margin:8px 0;">
    <div style="color:#aaa;font-size:11px;">Rank: {student.get('intelligence_rank','Unranked')}</div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio("📂 ERP Sections", [
    "Academic History", "AI Grade Predictor", 
    "Attendance Burn-Down", "Deep Dive Analytics", "PDF Reports"
])

# =====================================================
# SECTION 1: ACADEMIC HISTORY (Persistent)
# =====================================================
if page == "Academic History":
    st.markdown('<h1 style="color:#00d2ff;">📑 Multi-Semester Academic Ledger</h1>', unsafe_allow_html=True)
    st.caption("Your SGPA data is permanently saved — survives page refreshes.")
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    cols = st.columns(4)
    for i in range(1, 9):
        with cols[(i-1) % 4]:
            history[f"Sem {i}"] = st.number_input(
                f"Semester {i}", 0.0, 10.0, history[f"Sem {i}"], step=0.1, key=f"sem_{i}"
            )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("💾 Save to Database", key="save_history"):
        save_semester_history(st.session_state.user_name, history)
        st.success("✅ Academic history saved permanently!")
        st.rerun()
    
    # Growth visualization
    valid_sems = {k: v for k, v in history.items() if v > 0}
    if valid_sems:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(valid_sems.keys()), y=list(valid_sems.values()),
            mode='lines+markers', line=dict(shape='hv', color='#00d2ff', width=3),
            marker=dict(size=12, symbol='diamond', color='#6a11cb', line=dict(width=2, color='#00d2ff')),
            name='Your SGPA'
        ))
        fig.add_hline(y=8.5, line_dash="dot", line_color="#ffd700", annotation_text="Target: 8.5")
        fig.update_layout(
            template="plotly_dark", title="Academic Growth Trajectory",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(range=[0, 10.5], gridcolor='rgba(255,255,255,0.05)'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            font=dict(family="Inter, sans-serif")
        )
        st.plotly_chart(fig, use_container_width=True)

# =====================================================
# SECTION 2: AI GRADE PREDICTOR (Ensemble ML)
# =====================================================
elif page == "AI Grade Predictor":
    st.markdown('<h1 style="color:#00d2ff;">🔮 Performance Forecaster</h1>', unsafe_allow_html=True)
    st.caption("Powered by ensemble ML (Random Forest + Gradient Boosting + Ridge)")
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        att = st.slider("Attendance %", 0, 100, 75, key="pred_att")
        mst = st.number_input("Average MST %", 0, 100, 80, key="pred_mst")
    with c2:
        study = st.slider("Self Study (Hrs/Day)", 0, 15, 5, key="pred_study")
        distraction = st.selectbox("Distraction Level", ["None", "Low", "Medium", "High"], key="pred_dist")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("⚡ Generate Forecast", key="gen_forecast"):
        pred = get_grade_prediction(att, mst, study, distraction)
        tier_label, tier_color = get_performance_tier(pred)
        
        # Save prediction
        save_prediction(st.session_state.user_name, att, mst, study, distraction, pred)
        st.session_state.last_prediction = {
            'attendance': att, 'mst': mst, 'study_hours': study,
            'distraction': distraction, 'predicted': pred
        }
        
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Predicted SGPA", pred, delta=round(pred - 8.5, 2))
        mc2.metric("Performance Tier", tier_label)
        mc3.metric("vs Target (8.5)", f"{'+' if pred >= 8.5 else ''}{round(pred - 8.5, 2)}")
        
        # Growth Graph with prediction
        x_vals = [k for k, v in history.items() if v > 0] + ["Predicted"]
        y_vals = [v for v in history.values() if v > 0] + [pred]
        
        if x_vals:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=x_vals, y=y_vals, mode='lines+markers',
                line=dict(shape='hv', color='#00d2ff', width=3),
                marker=dict(size=12, symbol='diamond', color='#6a11cb', line=dict(width=2, color='#00d2ff'))
            ))
            fig.add_hline(y=8.5, line_dash="dot", line_color="#ffd700", annotation_text="Target: 8.5")
            fig.update_layout(
                template="plotly_dark", title="Academic Velocity + Prediction",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(range=[0, 10.5], gridcolor='rgba(255,255,255,0.05)'),
                font=dict(family="Inter, sans-serif")
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Prediction History
    pred_hist = get_prediction_history(st.session_state.user_name, 5)
    if pred_hist:
        with st.expander("📊 Recent Predictions"):
            df = pd.DataFrame(pred_hist)[['attendance', 'mst_marks', 'study_hours', 'distraction', 'predicted_sgpa', 'created_at']]
            df.columns = ['Att%', 'MST%', 'Study Hrs', 'Distraction', 'Predicted SGPA', 'Date']
            st.dataframe(df, use_container_width=True)

# =====================================================
# SECTION 3: ATTENDANCE BURN-DOWN (CGC 75% Rule)
# =====================================================
elif page == "Attendance Burn-Down":
    st.markdown('<h1 style="color:#00d2ff;">📊 Attendance Burn-Down Calculator</h1>', unsafe_allow_html=True)
    st.caption("CGC Mohali requires 75% minimum attendance. Know your limits.")
    
    saved_att = load_attendance(st.session_state.user_name)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        total = st.number_input("Total Lectures Conducted", 0, 500, saved_att['total_lectures'], key="att_total")
    with c2:
        attended = st.number_input("Lectures Attended", 0, 500, saved_att['attended_lectures'], key="att_attended")
    with c3:
        upcoming = st.number_input("Remaining Lectures in Sem", 0, 200, 30, key="att_upcoming")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("🔥 Calculate Burn-Down", key="calc_burndown"):
        if attended > total:
            st.error("Attended can't exceed total lectures!")
        else:
            save_attendance(st.session_state.user_name, total, attended)
            result = calculate_burndown(total, attended, upcoming)
            
            # Status card
            status_class = f"status-{result['status']}"
            st.markdown(f'<div class="{status_class}">', unsafe_allow_html=True)
            st.markdown(f"### {result['message']}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Metrics
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Current %", f"{result['current_pct']}%")
            mc2.metric("Can Still Bunk", f"{result['can_bunk']} lectures")
            mc3.metric("Must Attend to Recover", f"{result['must_attend']} lectures")
            mc4.metric("Projected % (all attend)", f"{result['projected_pct']}%")
            
            # Timeline chart
            timeline = get_burndown_timeline(total, attended, upcoming)
            df_tl = pd.DataFrame(timeline)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_tl['lecture'], y=df_tl['attend_all'],
                mode='lines', name='Attend All', line=dict(color='#00ff88', width=2)))
            fig.add_trace(go.Scatter(x=df_tl['lecture'], y=df_tl['skip_all'],
                mode='lines', name='Skip All', line=dict(color='#ff4444', width=2, dash='dash')))
            fig.add_hline(y=75, line_dash="dot", line_color="#ffd700", annotation_text="75% Threshold")
            fig.update_layout(
                template="plotly_dark", title="Attendance Projection Scenarios",
                xaxis_title="Future Lectures", yaxis_title="Attendance %",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(range=[0, 105], gridcolor='rgba(255,255,255,0.05)'),
                font=dict(family="Inter, sans-serif")
            )
            st.plotly_chart(fig, use_container_width=True)

# =====================================================
# SECTION 4: DEEP DIVE ANALYTICS
# =====================================================
elif page == "Deep Dive Analytics":
    st.markdown('<h1 style="color:#00d2ff;">🔍 Subject-Level Intelligence</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    sub = st.selectbox("Select Course from CGC Registry", ALL_SUBJECTS, key="dd_subject")
    weak_topic = st.text_input("Struggling Topic", key="dd_topic")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("🧠 Generate AI Intelligence Report", key="gen_report"):
        if not weak_topic:
            st.warning("Please enter a topic you're struggling with.")
        else:
            with st.spinner("AI analyzing syllabus..."):
                query = f"I am a 4th Sem CSE student at CGC Mohali. Create a detailed, technical study plan for {sub} focusing on {weak_topic}. Include: 1) Key concepts to master 2) Practice problems 3) Time allocation 4) Resources."
                context = f"Student: {st.session_state.user_name}, CGPA: {cgpa}, Target: 9.2, Subject: {sub}"
                advice = get_ai_response(query, context)
                
                # Save to DB
                save_ai_report(st.session_state.user_name, sub, weak_topic, advice)
                st.session_state.last_ai_report = advice
                
                st.markdown(f"""
                <div class="glass-card">
                    <h3 style="color:#00d2ff;">📋 AI Study Plan — {sub}</h3>
                    <p style="color:#aaa;font-size:12px;">Topic: {weak_topic} | Generated just now</p>
                    <hr>
                    <div style="color:#e0e0e8;line-height:1.8;">{advice}</div>
                </div>
                """, unsafe_allow_html=True)

# =====================================================
# SECTION 5: PDF REPORTS
# =====================================================
elif page == "PDF Reports":
    st.markdown('<h1 style="color:#00d2ff;">📄 Export Professional Reports</h1>', unsafe_allow_html=True)
    st.caption("Download your academic data and AI study plans as a branded PDF.")
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("#### Report Contents")
    inc_history = st.checkbox("Include Semester History", True)
    inc_prediction = st.checkbox("Include Latest Prediction", True)
    inc_graph = st.checkbox("Include Growth Chart", True)
    inc_ai = st.checkbox("Include AI Study Plan", True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("📥 Generate PDF Report", key="gen_pdf"):
        with st.spinner("Generating professional report..."):
            # Prepare data
            pred_data = st.session_state.last_prediction if inc_prediction else None
            
            # Get AI report text
            ai_text = None
            if inc_ai:
                report = get_latest_report(st.session_state.user_name)
                if report:
                    ai_text = report.get('report_content', '')
                elif st.session_state.last_ai_report:
                    ai_text = st.session_state.last_ai_report
            
            # Generate growth graph image for PDF
            graph_path = None
            if inc_graph:
                valid_sems = {k: v for k, v in history.items() if v > 0}
                if valid_sems:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=list(valid_sems.keys()), y=list(valid_sems.values()),
                        mode='lines+markers', line=dict(shape='hv', color='#00d2ff', width=3),
                        marker=dict(size=12, symbol='diamond', color='#6a11cb', line=dict(width=2, color='#00d2ff'))
                    ))
                    fig.add_hline(y=8.5, line_dash="dot", line_color="#ffd700")
                    fig.update_layout(
                        template="plotly_dark", title="Academic Growth",
                        width=800, height=400,
                        paper_bgcolor='#0d0d1a', plot_bgcolor='#0d0d1a',
                        yaxis=dict(range=[0, 10.5])
                    )
                    graph_path = os.path.join(tempfile.mkdtemp(), "growth_chart.png")
                    try:
                        fig.write_image(graph_path)
                    except Exception:
                        graph_path = None
            
            # Generate PDF
            try:
                pdf_bytes = generate_academic_report(
                    student_name=st.session_state.user_name,
                    semester_history=history if inc_history else {},
                    prediction_data=pred_data,
                    ai_report_text=ai_text,
                    graph_image_path=graph_path
                )
                
                st.success("✅ Report generated successfully!")
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"NAV_AI_Report_{st.session_state.user_name}.pdf",
                    mime="application/pdf",
                    key="download_pdf"
                )
            except Exception as e:
                st.error(f"PDF generation error: {str(e)}")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align:center;padding:10px;">
    <span style="color:#666;font-size:11px;">NAV-AI Pro v2.0</span><br>
    <span style="color:#444;font-size:10px;">Built by Naveen • CGC Mohali</span>
</div>
""", unsafe_allow_html=True)