"""
NAV-AI Pro — Understanding Level Assessment Engine (NLE)

Core Algorithm: Normalized Learning Efficiency (NLE)
=====================================================
Problem: Student A understands topic X in 1 hour, Student B needs 4 hours.
         Raw time comparison is UNFAIR.

Solution: We measure QUALITY of understanding (via adaptive quiz) and normalize
          speed against each student's OWN historical baseline — not against others.

Formula:
  comprehension_score = (correct / total) * 100   (weighted by difficulty)
  speed_ratio = baseline_time / actual_time        (>1 = faster than usual, <1 = slower)
  understanding_index = comprehension_score * 0.70 + speed_efficiency * 0.30

  where speed_efficiency = min(speed_ratio * 50, 100)  (capped at 100)

Why this is fair:
  - A slow learner who gets 100% accuracy scores HIGH because comprehension dominates (70%)
  - Speed is measured against THEIR OWN baseline, not against faster students
  - Over time, as their baseline shifts, the system adapts to their natural pace
"""
import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def generate_quiz_questions(subject, topic, difficulty='medium', count=5):
    """
    Use AI to generate adaptive quiz questions for a given topic.
    Returns a list of question dicts with options and correct answer.
    Falls back to template questions if AI is unavailable.
    """
    api_key = os.getenv("AI_API_KEY")

    if not api_key or "your_key" in api_key:
        return _fallback_questions(subject, topic, count)

    difficulty_instruction = {
        'easy': 'basic conceptual questions that test fundamental understanding',
        'medium': 'moderate questions that test application and analysis',
        'hard': 'advanced questions requiring synthesis, critical thinking, and edge cases'
    }

    prompt = f"""Generate exactly {count} multiple-choice questions to test understanding of "{topic}" in {subject}.

Difficulty: {difficulty_instruction.get(difficulty, difficulty_instruction['medium'])}

IMPORTANT: Return ONLY a valid JSON array. No markdown, no code fences, no extra text.
Each object must have exactly these keys:
- "question": the question text
- "options": array of exactly 4 option strings
- "correct": index of correct option (0-3)
- "difficulty": "{difficulty}"
- "explanation": brief 1-line explanation of correct answer

Example format:
[{{"question":"What is...","options":["A","B","C","D"],"correct":0,"difficulty":"{difficulty}","explanation":"Because..."}}]"""

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert quiz generator for Indian engineering students. Generate precise, educational MCQs. Return ONLY valid JSON array, no extra text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        questions = json.loads(raw)

        # Validate structure
        validated = []
        for q in questions[:count]:
            if all(k in q for k in ('question', 'options', 'correct')):
                validated.append({
                    'question': str(q['question']),
                    'options': [str(o) for o in q['options'][:4]],
                    'correct': int(q['correct']) % 4,
                    'difficulty': q.get('difficulty', difficulty),
                    'explanation': q.get('explanation', '')
                })
        return validated if validated else _fallback_questions(subject, topic, count)

    except Exception as e:
        print(f"[NLE] AI quiz generation failed: {e}")
        return _fallback_questions(subject, topic, count)


def _fallback_questions(subject, topic, count=5):
    """Template-based fallback when AI is unavailable."""
    templates = [
        {
            "question": f"Which of the following best describes the core concept of {topic} in {subject}?",
            "options": [
                f"A fundamental principle of {topic}",
                f"An advanced application of {topic}",
                f"A deprecated concept in {subject}",
                f"An unrelated concept to {subject}"
            ],
            "correct": 0,
            "difficulty": "easy",
            "explanation": f"This tests basic recognition of {topic}."
        },
        {
            "question": f"What is the primary advantage of understanding {topic}?",
            "options": [
                "It has no practical use",
                f"It forms the foundation for advanced {subject} concepts",
                "It is only useful for exams",
                "It is optional knowledge"
            ],
            "correct": 1,
            "difficulty": "easy",
            "explanation": f"{topic} is foundational to {subject}."
        },
        {
            "question": f"In what scenario would {topic} be most applicable?",
            "options": [
                "Never in real-world applications",
                f"Only in theoretical {subject} problems",
                f"In practical {subject} implementations and problem-solving",
                "Only during examinations"
            ],
            "correct": 2,
            "difficulty": "medium",
            "explanation": f"{topic} has extensive practical applications."
        },
        {
            "question": f"Which statement about {topic} in {subject} is FALSE?",
            "options": [
                f"{topic} is a key concept in {subject}",
                f"{topic} has real-world applications",
                f"{topic} requires no prerequisite knowledge",
                f"{topic} builds on fundamental principles"
            ],
            "correct": 2,
            "difficulty": "medium",
            "explanation": "Most topics require some prerequisite understanding."
        },
        {
            "question": f"How does {topic} relate to other concepts in {subject}?",
            "options": [
                "It is completely isolated",
                "It only connects to one other concept",
                f"It interconnects with multiple {subject} concepts",
                "It replaces all other concepts"
            ],
            "correct": 2,
            "difficulty": "hard",
            "explanation": f"Concepts in {subject} are interconnected."
        }
    ]
    return templates[:count]


def calculate_understanding_index(correct, total, time_taken_seconds, baseline_time_per_q, difficulty='medium'):
    """
    Calculate the Normalized Learning Efficiency (NLE) Understanding Index.

    Args:
        correct: number of correct answers
        total: total questions
        time_taken_seconds: total time spent on quiz
        baseline_time_per_q: student's personal average time per question for this subject
        difficulty: quiz difficulty level

    Returns:
        dict with comprehension_score, speed_ratio, understanding_index, tier
    """
    if total == 0:
        return {'comprehension_score': 0, 'speed_ratio': 1.0, 'understanding_index': 0, 'tier': 'Not Assessed'}

    # --- Comprehension Score (0-100) ---
    # Weight by difficulty: hard correct answers are worth more
    difficulty_weight = {'easy': 0.8, 'medium': 1.0, 'hard': 1.3}
    weight = difficulty_weight.get(difficulty, 1.0)
    raw_accuracy = correct / total
    comprehension_score = min(100, raw_accuracy * weight * 100)

    # --- Speed Ratio (normalized against self) ---
    actual_time_per_q = time_taken_seconds / total
    # If baseline is 30s and student took 15s → speed_ratio = 2.0 (faster than usual)
    # If baseline is 30s and student took 60s → speed_ratio = 0.5 (slower than usual)
    speed_ratio = baseline_time_per_q / max(actual_time_per_q, 1)

    # Convert to efficiency score (0-100), capped
    # speed_ratio of 1.0 = at baseline = 50 efficiency
    # speed_ratio of 2.0 = twice as fast = 100 efficiency
    speed_efficiency = min(100, speed_ratio * 50)

    # --- Understanding Index (0-100) ---
    # Comprehension dominates (70%) because QUALITY > SPEED
    understanding_index = round(comprehension_score * 0.70 + speed_efficiency * 0.30, 1)

    # --- Tier Classification ---
    if understanding_index >= 90:
        tier = '🧠 Mastered'
    elif understanding_index >= 75:
        tier = '⚡ Strong'
    elif understanding_index >= 60:
        tier = '📈 Developing'
    elif understanding_index >= 40:
        tier = '🔄 Needs Practice'
    else:
        tier = '🚨 Needs Work'

    return {
        'comprehension_score': round(comprehension_score, 1),
        'speed_ratio': round(speed_ratio, 2),
        'speed_efficiency': round(speed_efficiency, 1),
        'understanding_index': round(understanding_index, 1),
        'tier': tier,
        'accuracy_pct': round(raw_accuracy * 100, 1),
        'avg_time_per_q': round(actual_time_per_q, 1)
    }


def get_understanding_insights(index_data, subject, topic):
    """Generate human-readable insights from the understanding index."""
    ui = index_data['understanding_index']
    sr = index_data['speed_ratio']
    cs = index_data['comprehension_score']

    insights = []

    # Accuracy insight
    if cs >= 90:
        insights.append(f"🎯 Excellent accuracy! You clearly grasp {topic} well.")
    elif cs >= 70:
        insights.append(f"✅ Good accuracy on {topic}. A few concepts need reinforcement.")
    elif cs >= 50:
        insights.append(f"📚 Average accuracy. Review the core concepts of {topic} again.")
    else:
        insights.append(f"⚠️ Low accuracy. Consider re-studying {topic} from scratch.")

    # Speed insight (compared to SELF, not others)
    if sr > 1.5:
        insights.append("⚡ You answered significantly faster than your usual pace — great improvement!")
    elif sr > 1.0:
        insights.append("👍 You're answering slightly faster than your baseline — good progress.")
    elif sr > 0.7:
        insights.append("⏱️ Your pace is near your baseline — consistent performance.")
    else:
        insights.append("🐢 You took longer than usual. That's OK if accuracy is high — depth over speed!")

    # Fairness insight
    if sr < 0.7 and cs >= 80:
        insights.append("💡 You're thorough and accurate even when taking your time. Quality over speed!")
    if sr > 1.5 and cs < 60:
        insights.append("⚡ Fast but inaccurate. Slow down and focus on understanding, not speed.")

    return insights
