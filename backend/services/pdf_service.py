"""
NAV-AI Pro — Professional PDF Report Generator
Uses fpdf2 to create branded academic reports.
"""
from fpdf import FPDF
import os
import tempfile
from datetime import datetime


class NavAIReport(FPDF):
    """Custom PDF class with NAV-AI Pro branding."""
    
    def header(self):
        # Brand header bar
        self.set_fill_color(13, 13, 26)  # Dark theme background
        self.rect(0, 0, 210, 30, 'F')
        
        # Title
        self.set_font('Helvetica', 'B', 18)
        self.set_text_color(0, 210, 255)  # Cyan accent
        self.cell(0, 15, 'NAV-AI Pro', ln=False, align='L')
        
        # Subtitle
        self.set_font('Helvetica', '', 10)
        self.set_text_color(180, 180, 200)
        self.cell(0, 15, 'Student ERP & AI Analytics', ln=True, align='R')
        
        # Separator line
        self.set_draw_color(106, 17, 203)  # Purple accent
        self.set_line_width(0.8)
        self.line(10, 30, 200, 30)
        self.ln(15)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Generated on {datetime.now().strftime("%d %B %Y, %I:%M %p")} | NAV-AI Pro v2.0', 
                  align='C')
    
    def section_title(self, title):
        """Add a styled section title."""
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(106, 17, 203)  # Purple
        self.cell(0, 10, title, ln=True)
        self.set_draw_color(37, 117, 252)
        self.set_line_width(0.4)
        self.line(self.get_x(), self.get_y(), self.get_x() + 60, self.get_y())
        self.ln(5)
    
    def info_row(self, label, value):
        """Add a label-value row."""
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(60, 60, 60)
        self.cell(50, 7, f'{label}:', ln=False)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 30, 30)
        self.cell(0, 7, str(value), ln=True)
    
    def body_text(self, text):
        """Add formatted body text with line wrapping."""
        self.set_font('Helvetica', '', 10)
        self.set_text_color(40, 40, 40)
        # Handle unicode gracefully
        safe_text = text.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 6, safe_text)
        self.ln(3)


def generate_academic_report(student_name, semester_history, prediction_data=None, 
                              ai_report_text=None, graph_image_path=None):
    """
    Generate a comprehensive PDF report.
    
    Args:
        student_name: Student's name
        semester_history: Dict like {'Sem 1': 9.2, 'Sem 2': 8.5, ...}
        prediction_data: Dict with prediction inputs/output (optional)
        ai_report_text: AI-generated study plan text (optional)
        graph_image_path: Path to a saved growth graph PNG (optional)
    
    Returns:
        bytes: PDF file content
    """
    pdf = NavAIReport()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # --- STUDENT PROFILE SECTION ---
    pdf.section_title('Student Profile')
    pdf.info_row('Name', student_name)
    pdf.info_row('Institution', 'CGC Mohali — B.Tech CSE')
    pdf.info_row('Report Date', datetime.now().strftime('%d %B %Y'))
    
    # Calculate CGPA
    valid = [v for v in semester_history.values() if v > 0]
    cgpa = round(sum(valid) / len(valid), 2) if valid else 0.0
    pdf.info_row('Current CGPA', f'{cgpa} / 10.0')
    pdf.ln(5)
    
    # --- SEMESTER HISTORY TABLE ---
    pdf.section_title('Academic History')
    
    # Table header
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(240, 240, 250)
    pdf.set_text_color(30, 30, 30)
    col_width = 22
    for i in range(1, 9):
        pdf.cell(col_width, 8, f'Sem {i}', border=1, fill=True, align='C')
    pdf.ln()
    
    # Table data
    pdf.set_font('Helvetica', '', 10)
    for i in range(1, 9):
        val = semester_history.get(f'Sem {i}', 0.0)
        if val > 0:
            if val >= 8.5:
                pdf.set_text_color(0, 150, 0)
            elif val >= 7.0:
                pdf.set_text_color(200, 150, 0)
            else:
                pdf.set_text_color(200, 0, 0)
        else:
            pdf.set_text_color(150, 150, 150)
        pdf.cell(col_width, 8, f'{val:.1f}' if val > 0 else '—', border=1, align='C')
    pdf.set_text_color(30, 30, 30)
    pdf.ln(10)
    
    # --- GROWTH GRAPH ---
    if graph_image_path and os.path.exists(graph_image_path):
        pdf.section_title('Performance Growth Chart')
        pdf.image(graph_image_path, x=15, w=180)
        pdf.ln(10)
    
    # --- PREDICTION DATA ---
    if prediction_data:
        pdf.section_title('Latest AI Prediction')
        pdf.info_row('Attendance', f"{prediction_data.get('attendance', 'N/A')}%")
        pdf.info_row('MST Average', f"{prediction_data.get('mst', 'N/A')}%")
        pdf.info_row('Study Hours/Day', prediction_data.get('study_hours', 'N/A'))
        pdf.info_row('Distraction Level', prediction_data.get('distraction', 'N/A'))
        pdf.info_row('Predicted SGPA', f"{prediction_data.get('predicted', 'N/A')} / 10.0")
        pdf.ln(5)
    
    # --- AI STUDY PLAN ---
    if ai_report_text:
        pdf.add_page()
        pdf.section_title('AI-Generated Study Plan')
        pdf.body_text(ai_report_text)
    
    # Return as bytes
    return pdf.output()


def save_report_to_file(pdf_bytes, filename="NAV_AI_Report.pdf"):
    """Save PDF bytes to a temporary file and return the path."""
    tmp_dir = tempfile.mkdtemp()
    path = os.path.join(tmp_dir, filename)
    with open(path, 'wb') as f:
        f.write(pdf_bytes)
    return path
