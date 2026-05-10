/* =====================================================
   NAV-AI Pro — Frontend Application Logic
   ===================================================== */

const API = async (path, opts) => {
    try {
        const res = await fetch(path, opts);
        if (!res.ok) throw new Error(`Server error (${res.status})`);
        return await res.json();
    } catch (err) {
        toast(err.message || 'Network error', 'error');
        throw err;
    }
};
let charts = {};

function getName() { return document.getElementById('studentName').value.trim() || 'Naveen'; }

// ===== TOAST SYSTEM =====
function toast(msg, type = 'info') {
    const container = document.getElementById('toastContainer');
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    const icons = { success: 'ri-check-line', error: 'ri-error-warning-line', info: 'ri-information-line' };
    el.innerHTML = `<i class="${icons[type] || icons.info}" style="font-size:18px"></i><span>${msg}</span>`;
    container.appendChild(el);
    setTimeout(() => { el.classList.add('hide'); setTimeout(() => el.remove(), 350); }, 3500);
}

// ===== DATE & GREETING =====
function updateGreeting() {
    const name = getName();
    const h = new Date().getHours();
    let greet = 'Good evening';
    if (h < 12) greet = 'Good morning';
    else if (h < 17) greet = 'Good afternoon';
    document.getElementById('greetingText').textContent = `${greet}, ${name}`;

    const now = new Date();
    const opts = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('currentDate').textContent = now.toLocaleDateString('en-IN', opts);
}

// ===== NAVIGATION =====
function navigate(page) {
    document.querySelectorAll('.page').forEach(p => { p.classList.add('hidden'); });
    const el = document.getElementById('page-' + page);
    if (el) {
        el.classList.remove('hidden');
        el.style.animation = 'none'; void el.offsetWidth;
        el.style.animation = 'pageIn 0.4s cubic-bezier(0.16, 1, 0.3, 1)';
    }
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`)?.classList.add('active');

    const subtitles = {
        dashboard: "Here's your academic overview",
        predictor: 'Forecast your next semester SGPA',
        attendance: 'Track your CGC 75% attendance rule',
        analytics: 'AI-powered study plans tailored to you',
        understanding: 'Test and track your understanding level',
        reports: 'Export your data as professional PDFs'
    };
    document.getElementById('greetingSub').textContent = subtitles[page] || '';

    if (page === 'analytics') loadSubjects();
    if (page === 'attendance') loadAttendance();
    if (page === 'reports') loadPastReports();
    if (page === 'understanding') { loadQuizSubjects(); loadAssessmentHistory(); }
}

// ===== LOAD STUDENT DATA =====
async function loadStudentData() {
    updateGreeting();
    try {
        const name = getName();
        const data = await API(`/api/student/${encodeURIComponent(name)}`);

        // Animate CGPA
        const cgpaEl = document.getElementById('cgpaDisplay');
        animateValue(cgpaEl, 0, data.cgpa, 800);

        document.getElementById('tierDisplay').textContent = 'CGPA \u2022 ' + data.tier;
        document.getElementById('rankDisplay').textContent = 'Rank: ' + (data.student.intelligence_rank || 'Unranked');
        renderSemesterInputs(data.history);
        renderGrowthChart(data.history);
        loadPredHistory();
    } catch (e) { /* toast already shown */ }
}

// ===== ANIMATED COUNTER =====
function animateValue(el, start, end, duration) {
    const range = end - start;
    const startTime = performance.now();
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        const current = start + range * eased;
        el.textContent = current.toFixed(1);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ===== ACADEMIC LEDGER =====
function renderSemesterInputs(history) {
    const container = document.getElementById('semesterInputs');
    container.innerHTML = '';
    for (let i = 1; i <= 8; i++) {
        const val = history[`Sem ${i}`] || 0;
        container.innerHTML += `
        <div>
            <label class="input-label">Semester ${i}</label>
            <input id="sem${i}" type="number" min="0" max="10" step="0.1" value="${val}" class="input-field" placeholder="0.0">
        </div>`;
    }
}

function renderGrowthChart(history) {
    const labels = [], values = [];
    for (let i = 1; i <= 8; i++) {
        const v = history[`Sem ${i}`] || 0;
        if (v > 0) { labels.push(`Sem ${i}`); values.push(v); }
    }
    if (charts.growth) charts.growth.destroy();
    if (!labels.length) return;
    const ctx = document.getElementById('growthChart').getContext('2d');

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(108,99,255,0.12)');
    gradient.addColorStop(1, 'rgba(108,99,255,0)');

    charts.growth = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'SGPA', data: values,
                borderColor: '#6C63FF', backgroundColor: gradient,
                borderWidth: 2.5, pointRadius: 6, pointBackgroundColor: '#fff',
                pointBorderColor: '#6C63FF', pointBorderWidth: 2.5, tension: 0.3,
                fill: true
            }, {
                label: 'Target', data: Array(labels.length).fill(8.5),
                borderColor: '#E0DED8', borderWidth: 1.5, borderDash: [6, 4],
                pointRadius: 0, fill: false
            }]
        },
        options: chartOptions()
    });
}

async function saveHistory() {
    const btn = document.getElementById('saveHistoryBtn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px"></div> Saving...';
    try {
        const history = {};
        for (let i = 1; i <= 8; i++) history[`Sem ${i}`] = parseFloat(document.getElementById(`sem${i}`).value) || 0;
        await API(`/api/history/${encodeURIComponent(getName())}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ history })
        });
        toast('Academic history saved permanently!', 'success');
        loadStudentData();
    } catch (e) { /* toast already shown */ }
    btn.disabled = false;
    btn.innerHTML = '<i class="ri-save-line"></i>Save to Database';
}

// ===== GRADE PREDICTOR =====
async function runPrediction() {
    const btn = document.getElementById('predictBtn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px"></div> Predicting...';
    try {
        const body = {
            name: getName(),
            att: parseInt(document.getElementById('predAtt').value),
            mst: parseInt(document.getElementById('predMst').value),
            study: parseInt(document.getElementById('predStudy').value),
            distraction: document.getElementById('predDist').value
        };
        const data = await API('/api/predict', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
        });
        document.getElementById('predResults').classList.remove('hidden');

        const sgpaEl = document.getElementById('predSGPA');
        animateValue(sgpaEl, 0, data.predicted, 600);
        sgpaEl.style.color = data.color;

        document.getElementById('predTier').textContent = data.tier;
        const delta = (data.predicted - 8.5).toFixed(2);
        const deltaEl = document.getElementById('predDelta');
        deltaEl.textContent = (delta >= 0 ? '+' : '') + delta;
        deltaEl.style.color = delta >= 0 ? '#10b981' : '#ef4444';

        renderPredChart(data.history, data.predicted);
        loadPredHistory();
        loadStudentData();
        toast('Prediction generated successfully!', 'success');
    } catch (e) { /* toast already shown */ }
    btn.disabled = false;
    btn.innerHTML = '<i class="ri-sparkling-line"></i>Generate Forecast';
}

function renderPredChart(history, predicted) {
    const labels = [], values = [];
    for (let i = 1; i <= 8; i++) {
        const v = history[`Sem ${i}`] || 0;
        if (v > 0) { labels.push(`Sem ${i}`); values.push(v); }
    }
    labels.push('Predicted'); values.push(predicted);
    if (charts.pred) charts.pred.destroy();
    const ctx = document.getElementById('predChart').getContext('2d');

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(108,99,255,0.12)');
    gradient.addColorStop(1, 'rgba(108,99,255,0)');

    charts.pred = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'SGPA', data: values,
                borderColor: '#6C63FF', backgroundColor: gradient,
                borderWidth: 2.5, pointRadius: 6, pointBackgroundColor: '#fff',
                pointBorderColor: '#6C63FF', pointBorderWidth: 2.5, tension: 0.3, fill: true
            }, {
                label: 'Target', data: Array(labels.length).fill(8.5),
                borderColor: '#E0DED8', borderWidth: 1.5, borderDash: [6, 4],
                pointRadius: 0, fill: false
            }]
        },
        options: chartOptions()
    });
}

async function loadPredHistory() {
    try {
        const rows = await API(`/api/predictions/${encodeURIComponent(getName())}`);
        const card = document.getElementById('predHistoryCard');
        if (!rows.length) { card.classList.add('hidden'); return; }
        card.classList.remove('hidden');
        const tbody = document.querySelector('#predHistoryTable tbody');
        tbody.innerHTML = rows.map(r => {
            const badgeClass = r.distraction === 'High' ? 'badge-red' : r.distraction === 'Medium' ? 'badge-amber' : 'badge-green';
            return `<tr>
                <td>${r.attendance}%</td><td>${r.mst_marks}%</td><td>${r.study_hours}h</td>
                <td><span class="badge ${badgeClass}">${r.distraction}</span></td>
                <td style="font-weight:800;color:#6C63FF">${r.predicted_sgpa}</td>
                <td style="color:var(--text-muted);font-size:12px">${new Date(r.created_at).toLocaleDateString()}</td>
            </tr>`;
        }).join('');
    } catch (e) { /* toast already shown */ }
}

// ===== ATTENDANCE BURN-DOWN =====
async function loadAttendance() {
    try {
        const data = await API(`/api/attendance/${encodeURIComponent(getName())}`);
        if (data.total_lectures) document.getElementById('attTotal').value = data.total_lectures;
        if (data.attended_lectures) document.getElementById('attAttended').value = data.attended_lectures;
    } catch (e) { /* toast already shown */ }
}

async function calcBurndown() {
    const total = parseInt(document.getElementById('attTotal').value);
    const attended = parseInt(document.getElementById('attAttended').value);
    const upcoming = parseInt(document.getElementById('attUpcoming').value);
    if (attended > total) { toast('Attended cannot exceed total lectures!', 'error'); return; }

    const btn = document.getElementById('burndownBtn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px"></div> Calculating...';
    try {
        const data = await API(`/api/attendance/${encodeURIComponent(getName())}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ total, attended, upcoming })
        });
        const b = data.burndown;
        document.getElementById('attResults').classList.remove('hidden');

        const sc = document.getElementById('attStatusCard');
        sc.className = `card status-${b.status}`;
        sc.style.padding = '20px';
        sc.style.marginBottom = '16px';
        sc.innerHTML = `<div style="display:flex;align-items:center;gap:12px">
            <i class="ri-${b.status === 'safe' ? 'shield-check' : b.status === 'warning' ? 'alarm-warning' : 'error-warning'}-line" style="font-size:24px"></i>
            <p style="font-size:15px;font-weight:700">${b.message}</p>
        </div>`;

        document.getElementById('attPct').textContent = b.current_pct + '%';
        document.getElementById('attBunk').textContent = b.can_bunk;
        document.getElementById('attMust').textContent = b.must_attend;
        document.getElementById('attProj').textContent = b.projected_pct + '%';
        renderAttChart(data.timeline);
        toast('Burn-down calculated!', 'success');
    } catch (e) { /* toast already shown */ }
    btn.disabled = false;
    btn.innerHTML = '<i class="ri-fire-line"></i>Calculate Burn-Down';
}

function renderAttChart(timeline) {
    if (charts.att) charts.att.destroy();
    const ctx = document.getElementById('attChart').getContext('2d');
    charts.att = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeline.map(t => t.lecture),
            datasets: [{
                label: 'Attend All', data: timeline.map(t => t.attend_all),
                borderColor: '#10b981', borderWidth: 2, pointRadius: 0, fill: false
            }, {
                label: 'Skip All', data: timeline.map(t => t.skip_all),
                borderColor: '#ef4444', borderWidth: 2, borderDash: [5, 3], pointRadius: 0, fill: false
            }, {
                label: '75% Threshold', data: timeline.map(() => 75),
                borderColor: '#E0DED8', borderWidth: 1.5, borderDash: [6, 4], pointRadius: 0, fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { min: 0, max: 105, grid: { color: '#F5F3EF' }, title: { display: true, text: 'Attendance %', font: { size: 11, weight: 600 }, color: '#9CA3AF' } },
                x: { grid: { display: false }, title: { display: true, text: 'Future Lectures', font: { size: 11, weight: 600 }, color: '#9CA3AF' } }
            },
            plugins: { legend: { position: 'bottom', labels: { font: { size: 11, weight: 600 }, usePointStyle: true, pointStyle: 'circle', padding: 16 } } }
        }
    });
}

// ===== AI DEEP DIVE =====
async function loadSubjects() {
    const sel = document.getElementById('aiSubject');
    if (sel.options.length > 1) return;
    try {
        const data = await API('/api/subjects');
        sel.innerHTML = '';
        data.all.forEach(s => { const o = document.createElement('option'); o.value = s; o.textContent = s; sel.appendChild(o); });
    } catch (e) { /* toast already shown */ }
}

async function generateAIReport() {
    const subject = document.getElementById('aiSubject').value;
    const topic = document.getElementById('aiTopic').value.trim();
    if (!topic) { toast('Please enter a topic you are struggling with.', 'error'); return; }

    const btn = document.getElementById('aiGenBtn');
    btn.disabled = true;
    document.getElementById('aiLoading').classList.remove('hidden');
    document.getElementById('aiResult').classList.add('hidden');

    try {
        const data = await API('/api/ai-report', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: getName(), subject, topic })
        });
        document.getElementById('aiLoading').classList.add('hidden');
        document.getElementById('aiResult').classList.remove('hidden');
        document.getElementById('aiMeta').textContent = `${subject} \u2022 ${topic}`;
        document.getElementById('aiContent').textContent = data.report;
        toast('AI study plan generated!', 'success');
    } catch (e) {
        document.getElementById('aiLoading').classList.add('hidden');
    }
    btn.disabled = false;
}

// ===== PDF REPORTS =====
function downloadPDF() {
    toast('Generating PDF report...', 'info');
    window.open(`/api/pdf/${encodeURIComponent(getName())}`, '_blank');
}

async function loadPastReports() {
    try {
        const reports = await API(`/api/reports/${encodeURIComponent(getName())}`);
        const card = document.getElementById('pastReportsCard');
        if (!reports.length) { card.classList.add('hidden'); return; }
        card.classList.remove('hidden');
        document.getElementById('pastReportsList').innerHTML = reports.map(r => `
            <div class="report-item">
                <div style="display:flex; justify-content:space-between; align-items:start">
                    <div>
                        <span style="font-weight:700;font-size:14px;color:var(--text-primary)">${r.subject}</span>
                        <span style="font-size:12px;color:var(--text-muted);margin-left:8px">${r.weak_topic}</span>
                    </div>
                    <span style="font-size:11px;color:var(--text-faint)">${new Date(r.created_at).toLocaleDateString()}</span>
                </div>
                <p style="font-size:12px;color:var(--text-muted);margin-top:8px;line-height:1.5">${(r.report_content || '').substring(0, 180)}...</p>
            </div>
        `).join('');
    } catch (e) { /* toast already shown */ }
}

// ===== CHART OPTIONS HELPER =====
function chartOptions() {
    return {
        responsive: true,
        scales: {
            y: { min: 0, max: 10.5, grid: { color: '#F5F3EF' }, ticks: { font: { size: 11 } } },
            x: { grid: { display: false }, ticks: { font: { size: 11 } } }
        },
        plugins: { legend: { display: false } },
        interaction: { intersect: false, mode: 'index' }
    };
}

// =====================================================
// UNDERSTANDING LEVEL ASSESSMENT — Quiz Engine
// =====================================================
let quizState = {
    questions: [],
    currentIndex: 0,
    answers: [],        // selected option per question
    startTime: null,
    timerInterval: null,
    subject: '',
    topic: '',
    difficulty: 'medium',
    questionStartTimes: []  // track time per question
};

function selectDifficulty(diff) {
    quizState.difficulty = diff;
    document.querySelectorAll('.diff-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.diff === diff);
    });
}

async function loadQuizSubjects() {
    const sel = document.getElementById('quizSubject');
    if (sel.options.length > 1) return;
    try {
        const data = await API('/api/subjects');
        sel.innerHTML = '';
        data.all.forEach(s => {
            const o = document.createElement('option');
            o.value = s; o.textContent = s; sel.appendChild(o);
        });
    } catch (e) { /* toast already shown */ }
}

async function startQuiz() {
    const subject = document.getElementById('quizSubject').value;
    const topic = document.getElementById('quizTopic').value.trim();
    if (!topic) { toast('Please enter a topic to test your understanding.', 'error'); return; }

    quizState.subject = subject;
    quizState.topic = topic;

    const btn = document.getElementById('startQuizBtn');
    btn.disabled = true;
    document.getElementById('quizSetup').style.display = 'none';
    document.getElementById('quizLoading').classList.remove('hidden');
    document.getElementById('quizResults').classList.add('hidden');

    try {
        const data = await API('/api/understanding/quiz', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subject, topic, difficulty: quizState.difficulty, count: 5 })
        });

        quizState.questions = data.questions;
        quizState.currentIndex = 0;
        quizState.answers = new Array(data.questions.length).fill(-1);
        quizState.questionStartTimes = new Array(data.questions.length).fill(0);
        quizState.startTime = Date.now();

        document.getElementById('quizLoading').classList.add('hidden');
        document.getElementById('quizActive').classList.remove('hidden');

        startTimer();
        renderQuestion();
        toast('Quiz generated! Good luck!', 'success');
    } catch (e) {
        document.getElementById('quizLoading').classList.add('hidden');
        document.getElementById('quizSetup').style.display = '';
    }
    btn.disabled = false;
}

function startTimer() {
    if (quizState.timerInterval) clearInterval(quizState.timerInterval);
    quizState.timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - quizState.startTime) / 1000);
        const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const ss = String(elapsed % 60).padStart(2, '0');
        document.getElementById('quizTimerText').textContent = `${mm}:${ss}`;
    }, 1000);
}

function renderQuestion() {
    const q = quizState.questions[quizState.currentIndex];
    const total = quizState.questions.length;
    const idx = quizState.currentIndex;

    // Track question start time
    quizState.questionStartTimes[idx] = Date.now();

    // Progress
    document.getElementById('quizProgress').textContent = `Question ${idx + 1} of ${total}`;
    document.getElementById('quizProgressBar').style.width = `${((idx + 1) / total) * 100}%`;

    // Question text
    document.getElementById('quizQuestion').textContent = q.question;

    // Options
    const optLabels = ['A', 'B', 'C', 'D'];
    const optContainer = document.getElementById('quizOptions');
    optContainer.innerHTML = q.options.map((opt, i) => `
        <div class="quiz-option ${quizState.answers[idx] === i ? 'selected' : ''}"
             onclick="selectOption(${i})">
            <div class="option-marker">${optLabels[i]}</div>
            <span>${opt}</span>
        </div>
    `).join('');

    // Nav buttons
    document.getElementById('prevBtn').disabled = idx === 0;
    if (idx === total - 1) {
        document.getElementById('nextBtn').classList.add('hidden');
        document.getElementById('submitQuizBtn').classList.remove('hidden');
    } else {
        document.getElementById('nextBtn').classList.remove('hidden');
        document.getElementById('submitQuizBtn').classList.add('hidden');
    }
}

function selectOption(optIndex) {
    quizState.answers[quizState.currentIndex] = optIndex;
    // Re-render to update visual
    const options = document.querySelectorAll('.quiz-option');
    options.forEach((el, i) => {
        el.classList.toggle('selected', i === optIndex);
    });
}

function nextQuestion() {
    if (quizState.currentIndex < quizState.questions.length - 1) {
        quizState.currentIndex++;
        renderQuestion();
    }
}

function prevQuestion() {
    if (quizState.currentIndex > 0) {
        quizState.currentIndex--;
        renderQuestion();
    }
}

async function submitQuiz() {
    clearInterval(quizState.timerInterval);
    const timeTaken = Math.floor((Date.now() - quizState.startTime) / 1000);

    // Check for unanswered
    const unanswered = quizState.answers.filter(a => a === -1).length;
    if (unanswered > 0) {
        if (!confirm(`You have ${unanswered} unanswered question(s). Submit anyway?`)) {
            startTimer();
            return;
        }
    }

    const btn = document.getElementById('submitQuizBtn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px"></div> Analyzing...';

    // Build question results
    const questionResults = quizState.questions.map((q, i) => ({
        question: q.question,
        options: q.options,
        correct: q.correct,
        selected: quizState.answers[i],
        is_correct: quizState.answers[i] === q.correct,
        difficulty: q.difficulty || quizState.difficulty,
        time_spent: Math.floor((Date.now() - (quizState.questionStartTimes[i] || quizState.startTime)) / 1000)
    }));

    try {
        const data = await API('/api/understanding/submit', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: getName(),
                subject: quizState.subject,
                topic: quizState.topic,
                difficulty: quizState.difficulty,
                questions: questionResults,
                time_taken_seconds: timeTaken
            })
        });

        document.getElementById('quizActive').classList.add('hidden');
        document.getElementById('quizResults').classList.remove('hidden');

        displayResults(data, timeTaken);
        loadAssessmentHistory();
        toast('Assessment complete!', 'success');
    } catch (e) {
        startTimer();
    }

    btn.disabled = false;
    btn.innerHTML = '<i class="ri-check-double-line"></i>Submit Assessment';
}

function displayResults(data, timeTaken) {
    const r = data.result;

    // Animate NLE score
    const scoreEl = document.getElementById('nleScore');
    animateValue(scoreEl, 0, r.understanding_index, 1200);

    // Animate ring
    const ring = document.getElementById('nleRing');
    const circumference = 326.73;
    const offset = circumference - (r.understanding_index / 100) * circumference;
    // Use the brand gradient as fallback if SVG gradient doesn't render
    ring.style.stroke = '';
    setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);

    // Tier
    document.getElementById('nleTier').textContent = r.tier;

    // Stats
    document.getElementById('nleAccuracy').textContent = r.accuracy_pct + '%';
    document.getElementById('nleComprehension').textContent = r.comprehension_score.toFixed(1);
    document.getElementById('nleSpeed').textContent = r.speed_ratio.toFixed(2) + 'x';

    const mm = Math.floor(timeTaken / 60);
    const ss = timeTaken % 60;
    document.getElementById('nleTime').textContent = `${mm}m ${ss}s`;

    // Color code speed
    const speedEl = document.getElementById('nleSpeed');
    if (r.speed_ratio >= 1.0) {
        speedEl.style.color = '#10b981';
    } else if (r.speed_ratio >= 0.7) {
        speedEl.style.color = '#D97706';
    } else {
        speedEl.style.color = '#EF4444';
    }

    // Insights
    const insightsEl = document.getElementById('nleInsights');
    insightsEl.innerHTML = data.insights.map(i =>
        `<div class="nle-insight">${i}</div>`
    ).join('');
}

function resetQuiz() {
    // Reset state
    quizState = {
        questions: [], currentIndex: 0, answers: [],
        startTime: null, timerInterval: null,
        subject: '', topic: '', difficulty: 'medium',
        questionStartTimes: []
    };

    // Reset UI
    document.getElementById('quizSetup').style.display = '';
    document.getElementById('quizActive').classList.add('hidden');
    document.getElementById('quizResults').classList.add('hidden');
    document.getElementById('quizTimerText').textContent = '00:00';

    // Reset ring
    const ring = document.getElementById('nleRing');
    ring.style.strokeDashoffset = 326.73;

    // Reset difficulty buttons
    selectDifficulty('medium');
}

async function loadAssessmentHistory() {
    try {
        const data = await API(`/api/understanding/history/${encodeURIComponent(getName())}`);
        const container = document.getElementById('assessmentHistoryContent');
        const card = document.getElementById('assessmentHistoryCard');

        if (!data.history || !data.history.length) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="ri-lightbulb-flash-line"></i>
                    <p>No assessments yet. Take your first understanding check!</p>
                </div>`;
            return;
        }

        card.classList.remove('hidden');

        // Summary cards first
        let summaryHtml = '';
        if (data.summary && data.summary.length) {
            summaryHtml = '<div class="grid grid-3" style="margin-bottom:20px;gap:12px">';
            data.summary.forEach(s => {
                const tierClass = getTierClass(s.tier);
                const barColor = getBarColor(s.understanding_index);
                summaryHtml += `
                    <div class="metric-card" style="text-align:left;padding:16px">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                            <span style="font-size:13px;font-weight:700;color:var(--text-primary)">${s.subject}</span>
                            <span class="nle-mini-badge ${tierClass}">${s.tier}</span>
                        </div>
                        <div style="font-size:11px;color:var(--text-muted);margin-bottom:8px">${s.topic}</div>
                        <div class="nle-bar">
                            <div class="nle-bar-fill" style="width:${s.understanding_index}%;background:${barColor}"></div>
                        </div>
                        <div style="font-size:20px;font-weight:900;color:var(--text-primary);margin-top:8px">${s.understanding_index}</div>
                    </div>`;
            });
            summaryHtml += '</div>';
        }

        // History table
        let tableHtml = `
            <div style="overflow-x:auto">
            <table class="assessment-history-table">
                <thead><tr>
                    <th>Subject</th><th>Topic</th><th>Score</th><th>Accuracy</th><th>Speed</th><th>Tier</th><th>Date</th>
                </tr></thead>
                <tbody>`;

        data.history.forEach(h => {
            const tierClass = getTierClass(h.tier);
            tableHtml += `<tr>
                <td style="font-weight:600">${h.subject}</td>
                <td>${h.topic}</td>
                <td style="font-weight:800;color:var(--brand-500)">${h.understanding_index}</td>
                <td>${h.correct_answers}/${h.total_questions}</td>
                <td>${h.speed_ratio}x</td>
                <td><span class="nle-mini-badge ${tierClass}">${h.tier}</span></td>
                <td style="font-size:12px;color:var(--text-muted)">${new Date(h.created_at).toLocaleDateString()}</td>
            </tr>`;
        });

        tableHtml += '</tbody></table></div>';
        container.innerHTML = summaryHtml + tableHtml;
    } catch (e) { /* toast already shown */ }
}

function getTierClass(tier) {
    if (tier.includes('Mastered')) return 'tier-mastered';
    if (tier.includes('Strong')) return 'tier-strong';
    if (tier.includes('Developing')) return 'tier-developing';
    if (tier.includes('Practice')) return 'tier-practice';
    return 'tier-needs-work';
}

function getBarColor(score) {
    if (score >= 90) return 'linear-gradient(90deg, #10b981, #34d399)';
    if (score >= 75) return 'linear-gradient(90deg, #3b82f6, #60a5fa)';
    if (score >= 60) return 'linear-gradient(90deg, #f59e0b, #fbbf24)';
    if (score >= 40) return 'linear-gradient(90deg, #f97316, #fb923c)';
    return 'linear-gradient(90deg, #ef4444, #f87171)';
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    updateGreeting();
    loadStudentData();
});
