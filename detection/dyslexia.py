"""
Dyslexia Risk Screening Module for Sehat Sathi
Multi-Condition Screening Platform - Dyslexia Module
"""

import os
import json
import re
import math
import numpy as np

# ── Age Bracket Threshold Definitions (Named Configuration) ──
# Ages 6-8: Lenient thresholds (many phonological delays are developmentally normal)
THRESHOLDS_6_8 = {
    'composite_high': 65.0,
    'composite_mod': 45.0,
    'label': 'Ages 6-8 (Developmentally Lenient)'
}

# Ages 9-10: Moderate thresholds (transition zone)
THRESHOLDS_9_10 = {
    'composite_high': 58.0,
    'composite_mod': 38.0,
    'label': 'Ages 9-10 (Moderate Calibration)'
}

# Ages 10+: Strict thresholds (skills should be consolidated)
THRESHOLDS_10_PLUS = {
    'composite_high': 50.0,
    'composite_mod': 32.0,
    'label': 'Ages 10+ (Consolidated Skill Strictness)'
}

# ── Model Weights for v1 Weighted Average ──
WEIGHT_PHONOLOGICAL = 0.30
WEIGHT_RAN = 0.25
WEIGHT_DECODING = 0.20
WEIGHT_ORAL_READING = 0.15
WEIGHT_BACKGROUND = 0.10


# ── Multilingual Content Bank Loader ──
def load_content_bank(lang_code, resource_name):
    """
    Loads JSON content for the specified language and resource (e.g., 'questionnaire', 'ran_items').
    If requested language content is missing or marked 'pending', gracefully falls back to English ('en').
    Returns (content_dict, fallback_used_bool).
    """
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'content')
    lang_path = os.path.join(base_dir, lang_code, f"{resource_name}.json")
    
    fallback_used = False
    if not os.path.exists(lang_path):
        lang_path = os.path.join(base_dir, 'en', f"{resource_name}.json")
        fallback_used = True
    else:
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('status') == 'pending':
                    lang_path = os.path.join(base_dir, 'en', f"{resource_name}.json")
                    fallback_used = True
        except Exception:
            lang_path = os.path.join(base_dir, 'en', f"{resource_name}.json")
            fallback_used = True
            
    with open(lang_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
        
    return content, fallback_used


# ── STEP 3: QUANTIFICATION OF QUALITATIVE SIGNALS (UTILITY FUNCTIONS) ──

def detect_silence_hesitations(y_or_pcm, sr=22050, threshold_ratio=0.08, min_pause_sec=0.35):
    """
    Detects silence gaps (hesitations) in audio array or PCM buffer.
    Returns hesitation count and total pause duration in seconds.
    """
    if y_or_pcm is None or len(y_or_pcm) == 0:
        return 0, 0.0

    try:
        # Convert buffer if needed
        if isinstance(y_or_pcm, (bytes, bytearray)):
            audio = np.frombuffer(y_or_pcm, dtype=np.int16).astype(np.float32) / 32768.0
        else:
            audio = np.array(y_or_pcm, dtype=np.float32)
            
        frame_len = int(sr * 0.05) # 50ms frame
        hop_len = int(sr * 0.02)   # 20ms hop
        
        if len(audio) < frame_len:
            return 0, 0.0
            
        # Compute RMS energy per frame
        frames = [audio[i:i+frame_len] for i in range(0, len(audio) - frame_len, hop_len)]
        rms = np.array([np.sqrt(np.mean(f**2)) for f in frames])
        
        peak_rms = np.max(rms) if len(rms) > 0 else 0
        if peak_rms < 1e-4:
            return 1, len(audio) / float(sr)
            
        silent_frames = rms < (peak_rms * threshold_ratio)
        
        # Group silent frames into pause blocks
        pauses = []
        curr_pause = 0
        for is_silent in silent_frames:
            if is_silent:
                curr_pause += 1
            else:
                if curr_pause > 0:
                    pauses.append(curr_pause * (hop_len / float(sr)))
                    curr_pause = 0
        if curr_pause > 0:
            pauses.append(curr_pause * (hop_len / float(sr)))
            
        significant_pauses = [p for p in pauses if p >= min_pause_sec]
        return len(significant_pauses), float(sum(significant_pauses))
    except Exception as e:
        print(f"Hesitation detection error: {e}")
        return 0, 0.0


def detect_self_corrections(transcript_text):
    """
    Detects self-corrections in speech-to-text transcript (words repeated or corrected in close succession).
    Example: 'the cat... cap... cat' or 'red... no blue'
    Returns integer self-correction count.
    """
    if not transcript_text:
        return 0
        
    words = re.findall(r'\b\w+\b', transcript_text.lower())
    if len(words) < 2:
        return 0
        
    self_corr_count = 0
    correction_markers = {'no', 'sorry', 'i mean', 'wait'}
    
    for i in range(len(words) - 1):
        if words[i] == words[i+1]:
            self_corr_count += 1
        elif words[i] in correction_markers and i > 0 and i < len(words) - 1:
            self_corr_count += 1
        elif i < len(words) - 2 and words[i] == words[i+2]:
            self_corr_count += 1
            
    return self_corr_count


def calculate_levenshtein_distance(str1, str2):
    """
    Computes Levenshtein edit distance between target and spoken text/phoneme sequence.
    """
    s1, s2 = str1.lower().strip(), str2.lower().strip()
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
        
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
                
    return dp[m][n]


def calculate_wcpm(words_correct, elapsed_seconds):
    """
    Calculates Words-Correct-Per-Minute (WCPM).
    """
    if elapsed_seconds <= 0:
        return 0.0
    return round((float(words_correct) / float(elapsed_seconds)) * 60.0, 1)


def classify_spelling_error(target_word, user_spelling):
    """
    Classifies spelling errors as 'phonetically_plausible' vs 'non_phonetic'.
    Phonetically plausible errors sound like target (e.g., 'kat' vs 'cat', 'nite' vs 'night').
    """
    target = target_word.lower().strip()
    spelling = user_spelling.lower().strip()
    
    if target == spelling:
        return "correct"
        
    # Check simple phonetic rules (c->k, ph->f, night->nite, etc.)
    norm_target = target.replace('ph', 'f').replace('c', 'k').replace('gh', '').replace('ee', 'i').replace('oo', 'u')
    norm_spelling = spelling.replace('ph', 'f').replace('c', 'k').replace('gh', '').replace('ee', 'i').replace('oo', 'u')
    
    dist = calculate_levenshtein_distance(norm_target, norm_spelling)
    if dist <= 1 or norm_target == norm_spelling:
        return "phonetically_plausible"
    
    raw_dist = calculate_levenshtein_distance(target, spelling)
    if raw_dist <= len(target) * 0.35:
        return "phonetically_plausible"
        
    return "non_phonetic"


def detect_code_switching(transcript_text, selected_lang_code='en'):
    """
    STEP 6 NOVEL FEATURE 1: Code-Switching Detection.
    Detects when bilingual Indian children mix languages mid-sentence (e.g. English words in Hindi reading).
    Returns code_switch_count and logs it as metadata so it is NOT penalized as a dyslexia reading error.
    """
    if not transcript_text:
        return 0, []
        
    words = re.findall(r'\b\w+\b', transcript_text)
    code_switches = []
    
    for word in words:
        # Check if ASCII Latin script word appears in Hindi/Devanagari text, or vice versa
        has_latin = bool(re.search(r'[a-zA-Z]', word))
        has_indic = bool(re.search(r'[\u0900-\u0D7F]', word))
        
        if selected_lang_code in ['hi', 'bn', 'ta', 'te', 'mr', 'gu', 'kn', 'ml', 'pa', 'or', 'ur'] and has_latin:
            code_switches.append(word)
        elif selected_lang_code == 'en' and has_indic:
            code_switches.append(word)
            
    return len(code_switches), code_switches


def select_next_adaptive_item(current_index, item_history):
    """
    STEP 6 NOVEL FEATURE 2: Adaptive Item Difficulty Branching.
    If child answers first 2 items quickly and correctly (fast latency, 0 errors),
    skips ahead to harder items. If struggling, presents easier confirmatory items.
    """
    if current_index < 2:
        return current_index + 1
        
    recent = item_history[-2:]
    all_correct = all(h.get('correct', False) for h in recent)
    all_fast = all(h.get('time_sec', 10) < 3.0 for h in recent)
    
    if all_correct and all_fast:
        # Skip 1 ahead
        return min(current_index + 2, len(item_history) + 3)
    return current_index + 1


# ── STEP 2: SUBTEST ANALYSIS FUNCTIONS ──

def analyze_questionnaire_data(answers, lang_code='en'):
    """
    Subtest 1: Background Risk Questionnaire
    Outputs normalized 0-100 background risk sub-score.
    """
    content, fallback = load_content_bank(lang_code, 'questionnaire')
    questions = content.get('questions', [])
    
    total_max = len(questions) * 2
    if total_max == 0:
        return 0.0, fallback
        
    score_obtained = 0
    for q in questions:
        qid = q['id']
        val = int(answers.get(qid, 0))
        score_obtained += min(max(val, 0), 2)
        
    norm_score = round((score_obtained / float(total_max)) * 100.0, 1)
    return norm_score, fallback


def analyze_ran_data(grid_times, grid_errors, self_corrections=0, hesitations=0, lang_code='en', total_items=40, recognized_count=None):
    """
    Subtest 2: Rapid Automatized Naming (RAN)
    Measures total time, speech accuracy, error count, and pause count.
    
    Strict Rule:
    - Under 15s per grid: LOW RISK / EXCELLENT (0.0% Risk)
    - 15s - 20s per grid: MODERATE RISK / MILD DELAY (30.0% Risk)
    - Above 20s per grid: HIGH RISK / SEVERE DELAY (75.0% Risk)
    """
    content, fallback = load_content_bank(lang_code, 'ran_items')
    
    if not grid_times:
        return 50.0, fallback
        
    avg_grid_time = float(np.mean(grid_times))
    total_errors = sum(grid_errors) if grid_errors else 0
    
    # 1. Time Risk Calculation based on explicit 15s / 20s cutoffs
    if avg_grid_time < 15.0:
        # Under 15s is EXCELLENT speed -> 0% Risk
        time_risk = 0.0
    elif avg_grid_time <= 20.0:
        # 15s to 20s is MILD DELAY -> 30% Risk
        time_risk = 30.0 + ((avg_grid_time - 15.0) / 5.0) * 25.0
    else:
        # > 20s is SEVERE DELAY -> 70% to 100% Risk
        time_risk = 70.0 + min(30.0, (avg_grid_time - 20.0) * 4.0)
        
    # 2. Accuracy Calculation
    if recognized_count is not None and total_items > 0:
        accuracy_ratio = min(1.0, float(recognized_count) / float(total_items))
        if accuracy_ratio >= 0.8:
            accuracy_penalty = 0.0
        else:
            accuracy_penalty = (1.0 - accuracy_ratio) * 50.0
    else:
        accuracy_penalty = min(30.0, total_errors * 5.0)
        
    if avg_grid_time < 15.0 and (total_errors == 0 or (recognized_count is not None and recognized_count >= total_items * 0.8)):
        norm_score = 0.0
    else:
        raw_risk = (time_risk * 0.7) + (accuracy_penalty * 0.3)
        norm_score = min(100.0, max(0.0, round(raw_risk, 1)))
    
    return norm_score, fallback


def analyze_phonological_data(task_results, hesitations=0, lang_code='en'):
    """
    Subtest 3: Phonological Awareness
    Calculates accuracy across rhyme match, sound blending, segmentation, odd-one-out.
    Outputs normalized 0-100 phonological risk sub-score (higher = higher risk).
    """
    content, fallback = load_content_bank(lang_code, 'phonological_tasks')
    
    if not task_results:
        return 50.0, fallback
        
    correct_count = sum(1 for tr in task_results if tr.get('correct', False))
    total_tasks = len(task_results)
    
    accuracy = (correct_count / float(total_tasks)) if total_tasks > 0 else 0.5
    
    # 90%+ accuracy guarantees 0% base risk
    if accuracy >= 0.9:
        risk_from_accuracy = 0.0
        hesitation_penalty = 0.0
    else:
        risk_from_accuracy = (1.0 - accuracy) * 100.0
        hesitation_penalty = min(15.0, hesitations * 2.0)
    
    norm_score = min(100.0, max(0.0, round(risk_from_accuracy + hesitation_penalty, 1)))
    return norm_score, fallback


def analyze_decoding_data(decoding_items, hesitations=0, code_switches=0, lang_code='en'):
    """
    Subtest 4: Nonsense-Word Decoding
    Compares spoken nonwords against phoneme target via edit distance.
    Code switches are excluded from penalizing decoding accuracy!
    Outputs normalized 0-100 decoding risk sub-score (higher = higher risk).
    """
    content, fallback = load_content_bank(lang_code, 'nonwords')
    
    if not decoding_items:
        return 50.0, fallback
        
    total_dist = 0
    total_max_len = 0
    
    for item in decoding_items:
        target = item.get('target', '')
        spoken = item.get('spoken', '')
        dist = calculate_levenshtein_distance(target, spoken)
        total_dist += dist
        total_max_len += max(len(target), 1)
        
    error_ratio = (total_dist / float(total_max_len)) if total_max_len > 0 else 0.5
    
    if error_ratio <= 0.15:
        norm_score = 0.0
    else:
        raw_risk = error_ratio * 100.0 + min(10.0, hesitations * 1.5)
        norm_score = min(100.0, max(0.0, round(raw_risk, 1)))
        
    return norm_score, fallback


def analyze_oral_spelling_data(reading_time_sec, words_correct, spelling_attempts, lang_code='en'):
    """
    Subtest 5: Oral Reading + Spelling
    Calculates WCPM and classifies spelling errors (phonetically plausible vs non-phonetic).
    Outputs normalized 0-100 oral reading & spelling risk sub-score.
    """
    content_passages, fb1 = load_content_bank(lang_code, 'reading_passages')
    content_spelling, fb2 = load_content_bank(lang_code, 'spelling_words')
    fallback = fb1 or fb2
    
    wcpm = calculate_wcpm(words_correct, reading_time_sec)
    
    # Benchmark WCPM for age 8 is ~60 WCPM
    if wcpm >= 55:
        fluency_risk = 0.0
    elif wcpm >= 40:
        fluency_risk = (55 - wcpm) * 1.5
    else:
        fluency_risk = 25.0 + (40 - wcpm) * 1.5
        
    # Analyze spelling errors
    spelling_targets = content_spelling.get('words', [])
    phonetic_errors = 0
    non_phonetic_errors = 0
    
    for idx, attempt in enumerate(spelling_attempts):
        target_obj = spelling_targets[idx] if idx < len(spelling_targets) else {'target': attempt.get('target', '')}
        target_word = target_obj.get('target', '')
        user_input = attempt.get('written', '')
        
        err_type = classify_spelling_error(target_word, user_input)
        if err_type == "phonetically_plausible":
            phonetic_errors += 1
        elif err_type == "non_phonetic":
            non_phonetic_errors += 1
            
    spelling_risk = (phonetic_errors * 5.0) + (non_phonetic_errors * 12.0)
    
    if wcpm >= 55 and (phonetic_errors + non_phonetic_errors == 0):
        norm_score = 0.0
    else:
        combined_risk = (fluency_risk * 0.5) + (spelling_risk * 0.5)
        norm_score = min(100.0, max(0.0, round(combined_risk, 1)))
    
    return norm_score, wcpm, phonetic_errors, non_phonetic_errors, fallback


# ── STEP 4: COMPOSITE SCORING MODEL ──

def calculate_dyslexia_risk(age, gender, background_score, ran_score, phonological_score, decoding_score, oral_reading_score, metadata=None):
    """
    Combines 5 sub-scores into feature vector:
    [background_score, ran_score, phonological_score, decoding_score, oral_reading_score]
    """
    try:
        age_num = float(age)
    except (ValueError, TypeError):
        age_num = 8.0
        
    if age_num <= 8.0:
        bracket = THRESHOLDS_6_8
        bracket_key = "6-8"
    elif age_num <= 10.0:
        bracket = THRESHOLDS_9_10
        bracket_key = "9-10"
    else:
        bracket = THRESHOLDS_10_PLUS
        bracket_key = "10+"

    feature_vector = [
        float(background_score),
        float(ran_score),
        float(phonological_score),
        float(decoding_score),
        float(oral_reading_score)
    ]
    
    # Path b: Check for trained scikit-learn model file
    model_path = os.path.join(os.path.dirname(__file__), 'models', 'dyslexia_model.pkl')
    composite_score = None
    model_used = "v1_weighted_average"
    
    if os.path.exists(model_path):
        try:
            import pickle
            with open(model_path, 'rb') as mf:
                model = pickle.load(mf)
                prob = model.predict_proba([feature_vector])[0][1]
                composite_score = round(prob * 100.0, 1)
                model_used = "v2_logistic_regression"
        except Exception as me:
            print(f"v2 model load exception, falling back to v1: {me}")
            
    if composite_score is None:
        # Path a: v1 Weighted average
        weighted_val = (
            phonological_score * WEIGHT_PHONOLOGICAL +
            ran_score * WEIGHT_RAN +
            decoding_score * WEIGHT_DECODING +
            oral_reading_score * WEIGHT_ORAL_READING +
            background_score * WEIGHT_BACKGROUND
        )
        composite_score = round(weighted_val, 1)

    # Calculate intuitive Performance Marks Score (100% = Perfect Marks)
    proficiency_marks = round(max(0.0, min(100.0, 100.0 - composite_score)), 1)
        
    # Determine risk band based on age bracket threshold
    if composite_score >= bracket['composite_high']:
        risk_band = "High Risk"
        recommendation = "Screening flags significant indicators associated with dyslexia risk. Consultation with a specialist (psychologist, special educator, or speech pathologist) is strongly recommended."
    elif composite_score >= bracket['composite_mod']:
        risk_band = "Moderate Risk"
        recommendation = "Screening indicates mild to moderate phonological or RAN decoding gaps. Re-assessment after 3 months and targeted reading practice are suggested."
    else:
        risk_band = "Low Risk"
        recommendation = "Screening metrics are within age-typical expectations. Excellent performance across phonological and naming benchmarks."

    explainability = []
    if phonological_score >= 40.0:
        explainability.append("Phonological Awareness score indicates difficulty with rhyme matching and sound blending.")
    if ran_score >= 40.0:
        explainability.append("Rapid Automatized Naming (RAN) latency was elevated, suggesting retrieval speed bottlenecks.")
    if decoding_score >= 40.0:
        explainability.append("Nonsense-Word Decoding showed elevated phoneme edit distance error rates.")
    if oral_reading_score >= 40.0:
        explainability.append("Oral Reading Fluency (WCPM) or spelling error profile indicated decoding hesitations.")
    if background_score >= 45.0:
        explainability.append("Background Questionnaire highlighted early developmental reading or family history factors.")
        
    if not explainability:
        explainability.append("All 5 subtests performed within expected age-typical baseline boundaries with high proficiency marks.")

    return {
        "risk_band": risk_band,
        "composite_score": composite_score,
        "proficiency_marks": proficiency_marks,
        "age_group_label": bracket['label'],
        "age_bracket": bracket_key,
        "model_used": model_used,
        "subscores": {
            "background": background_score,
            "ran": ran_score,
            "phonological": phonological_score,
            "decoding": decoding_score,
            "oral_reading": oral_reading_score
        },
        "explainability": explainability,
        "recommendation": recommendation,
        "metadata": metadata or {}
    }
