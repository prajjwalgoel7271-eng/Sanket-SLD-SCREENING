"""
Specific Learning Disorder (SLD) Age-Tiered Diagnostic Module for Sehat Sathi
Clinical Assessment Engine covering Tiers 1-4 across Dyslexia, Dyscalculia, and Dysgraphia.
Fully mapped to DSM-5-TR and ICD-11 diagnostic criteria.
"""

import os
import json
import math
import numpy as np

# ── DSM-5-TR & ICD-11 CRITERIA MAPPING TABLE ──
DSM_ICD_MAPPING = {
    "tier1_phonological": {
        "dsm5": "DSM-5-TR Risk Flag: Pre-Literate Phonological Awareness Deficit",
        "icd11": "ICD-11: 6A03.Z Developmental learning disorder, unspecified (Precursor Risk)",
        "criterion": "Criterion A1: Inaccuracy or slowness in phonological sound discrimination and rhyming."
    },
    "tier1_numerical": {
        "dsm5": "DSM-5-TR Risk Flag: Early Non-Symbolic Number Sense Deficit",
        "icd11": "ICD-11: 6A03.1 Risk for Learning Disorder in Mathematics",
        "criterion": "Criterion A3: Difficulty mastering number sense and instant non-symbolic subitizing."
    },
    "tier1_motor": {
        "dsm5": "DSM-5-TR Risk Flag: Visuomotor & Midline Integration Delay",
        "icd11": "ICD-11: 6A04 Developmental motor coordination disorder (Visuomotor/Midline)",
        "criterion": "Criterion A4: Impaired visuomotor coordination across visual midline trajectory."
    },
    "dyslexia": {
        "dsm5": "DSM-5-TR: 315.00 Specific Learning Disorder With Impairment in Reading",
        "icd11": "ICD-11: 6A03.0 Developmental learning disorder with impairment in reading",
        "criterion": "Criteria A1 & A2: Inaccurate or slow and effortful word reading, decoding, and reading comprehension."
    },
    "dyscalculia": {
        "dsm5": "DSM-5-TR: 315.1 Specific Learning Disorder With Impairment in Mathematics",
        "icd11": "ICD-11: 6A03.1 Developmental learning disorder with impairment in mathematics",
        "criterion": "Criteria A3 & A4: Difficulties mastering number sense, number facts, calculation, or math reasoning."
    },
    "dysgraphia": {
        "dsm5": "DSM-5-TR: 315.2 Specific Learning Disorder With Impairment in Written Expression",
        "icd11": "ICD-11: 6A03.2 Developmental learning disorder with impairment in written expression",
        "criterion": "Criteria A5 & A6: Difficulties with spelling accuracy, written expression clarity, and motor graphomotor speed decay."
    },
    "academic_distress": {
        "dsm5": "DSM-5-TR: Secondary Educational Distress & Academic Task Anxiety (V62.89 / Contextual)",
        "icd11": "ICD-11: QE52 Academic Underachievement & Educational Task Distress",
        "criterion": "Associated Feature: Academic task-specific anxiety, frustration, and avoidance behavior."
    }
}


def load_sld_content_bank(lang_code, tier_num):
    """
    Loads JSON content bank for specified language and tier.
    Falls back gracefully to English ('en') if language file is missing.
    """
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'content')
    lang_path = os.path.join(base_dir, lang_code, f"sld_tier{tier_num}.json")
    
    fallback = False
    if not os.path.exists(lang_path):
        lang_path = os.path.join(base_dir, 'en', f"sld_tier{tier_num}.json")
        fallback = True
        
    try:
        with open(lang_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        return content, fallback
    except Exception:
        fallback_path = os.path.join(base_dir, 'en', f"sld_tier{tier_num}.json")
        with open(fallback_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        return content, True


# ── TIER 1 EVALUATION ENGINE (Ages 3-5: Precursor Domains) ──
def analyze_tier1_data(rhyme_results, subitizing_results, motor_results):
    """
    Evaluates Tier 1 precursor screening.
    Outputs 3 separate domain risk flags (Phonological, Numerical, Motor-Visual).
    100% accuracy = Low Risk.
    """
    # 1. Phonological Precursor (Rhyme & Sound Discrimination Game)
    phon_correct = sum(1 for r in rhyme_results if r.get('correct', False))
    phon_total = max(1, len(rhyme_results))
    phon_acc = float((phon_correct / phon_total) * 100.0)
    phon_avg_time = float(np.mean([r.get('time_sec', 2.0) for r in rhyme_results])) if rhyme_results else 2.0

    if phon_acc >= 80.0:
        phon_risk = "Low Risk"
    elif phon_acc >= 50.0:
        phon_risk = "Moderate Risk"
    else:
        phon_risk = "High Risk"

    # 2. Numerical Precursor (Subitizing Task)
    sub_correct = sum(1 for s in subitizing_results if s.get('correct', False))
    sub_total = max(1, len(subitizing_results))
    sub_acc = float((sub_correct / sub_total) * 100.0)
    sub_avg_time = float(np.mean([s.get('time_sec', 1.5) for s in subitizing_results])) if subitizing_results else 1.5

    if sub_acc >= 80.0:
        num_risk = "Low Risk"
    elif sub_acc >= 50.0:
        num_risk = "Moderate Risk"
    else:
        num_risk = "High Risk"

    # 3. Motor & Visual Midline Crossing Task
    dev_px = float(motor_results.get('avg_deviation_px', 0.0))
    midline_pause = float(motor_results.get('midline_pause_sec', 0.0))
    completion_sec = float(motor_results.get('completion_time_sec', 5.0))

    if dev_px <= 25.0 and midline_pause <= 1.0:
        motor_risk = "Low Risk"
    elif dev_px <= 45.0:
        motor_risk = "Moderate Risk"
    else:
        motor_risk = "High Risk"

    return {
        "tier": 1,
        "age_group": "Ages 3-5 (Precursor Screening)",
        "domain_results": {
            "phonological_precursor": {
                "risk_band": phon_risk,
                "accuracy": round(phon_acc, 1),
                "avg_response_sec": round(phon_avg_time, 2),
                "dsm_icd": DSM_ICD_MAPPING["tier1_phonological"]
            },
            "numerical_precursor": {
                "risk_band": num_risk,
                "accuracy": round(sub_acc, 1),
                "avg_response_sec": round(sub_avg_time, 2),
                "subitizing_latency_flag": bool(sub_avg_time > 2.5),
                "dsm_icd": DSM_ICD_MAPPING["tier1_numerical"]
            },
            "motor_visual_midline": {
                "risk_band": motor_risk,
                "path_deviation_px": round(dev_px, 1),
                "midline_pause_sec": round(midline_pause, 2),
                "completion_time_sec": round(completion_sec, 2),
                "dsm_icd": DSM_ICD_MAPPING["tier1_motor"]
            }
        },
        "explainability": [
            f"Phonological Precursor: {phon_risk} ({phon_acc:.1f}% accuracy across rhyming trials).",
            f"Numerical Precursor: {num_risk} (Subitizing accuracy: {sub_acc:.1f}%, response latency: {sub_avg_time:.2f}s).",
            f"Motor/Midline Precursor: {motor_risk} (Average path deviation: {dev_px:.1f}px)."
        ]
    }


# ── TIER 2 EVALUATION ENGINE (Ages 6-9: Manifestation Screening) ──
def analyze_tier2_data(dyslexia_data, dyscalculia_data, dysgraphia_data):
    """
    Evaluates Tier 2 Manifestation across Dyslexia, Dyscalculia, and Dysgraphia branches.
    Accurate user answers (100% accuracy) yield Low Risk.
    """
    # --- 1. Dyslexia Branch ---
    comp_acc = float(dyslexia_data.get('comprehension_acc', dyslexia_data.get('comprehension_accuracy', 100.0)))
    spelling_acc = float(dyslexia_data.get('spelling_acc', dyslexia_data.get('spelling_accuracy', 100.0)))
    decoding_acc = float(dyslexia_data.get('decoding_accuracy', 100.0))
    ran_sec = float(dyslexia_data.get('ran_total_sec', 15.0))

    avg_dyslexia_acc = (comp_acc + spelling_acc + decoding_acc) / 3.0

    if avg_dyslexia_acc >= 85.0:
        dyslexia_band = "Low Risk"
        dyslexia_score = float(max(0.0, 100.0 - avg_dyslexia_acc))
    elif avg_dyslexia_acc >= 60.0:
        dyslexia_band = "Moderate Risk"
        dyslexia_score = float(100.0 - avg_dyslexia_acc)
    else:
        dyslexia_band = "High Risk"
        dyslexia_score = float(100.0 - avg_dyslexia_acc)

    # --- 2. Dyscalculia Branch ---
    mag_acc = float(dyscalculia_data.get('magnitude_accuracy', 100.0))
    fact_acc = float(dyscalculia_data.get('fact_accuracy', 100.0))
    seq_acc = float(dyscalculia_data.get('sequence_accuracy', 100.0))
    fact_calc_delay_count = int(dyscalculia_data.get('fact_calculation_delays', 0))

    avg_math_acc = (mag_acc + fact_acc + seq_acc) / 3.0

    if avg_math_acc >= 85.0 and fact_calc_delay_count <= 2:
        dyscalculia_band = "Low Risk"
        dyscalculia_score = float(max(0.0, 100.0 - avg_math_acc))
    elif avg_math_acc >= 60.0:
        dyscalculia_band = "Moderate Risk"
        dyscalculia_score = float(100.0 - avg_math_acc)
    else:
        dyscalculia_band = "High Risk"
        dyscalculia_score = float(100.0 - avg_math_acc)

    # --- 3. Dysgraphia Branch ---
    pause_ratio = float(dysgraphia_data.get('pause_duration_ratio', 0.15))
    speed_decay_pct = float(dysgraphia_data.get('speed_decay_pct', 0.0))
    jitter_px = float(dysgraphia_data.get('stroke_jitter_px', 2.0))

    # Sentence 2 is naturally longer than sentence 1; char-normalized speed decay < 30% is normal (Low Risk)
    if speed_decay_pct <= 30.0 and pause_ratio <= 0.40 and jitter_px <= 15.0:
        dysgraphia_band = "Low Risk"
        dysgraphia_score = float(speed_decay_pct * 0.3)
    elif speed_decay_pct <= 55.0 or pause_ratio <= 0.60:
        dysgraphia_band = "Moderate Risk"
        dysgraphia_score = float(speed_decay_pct * 0.6)
    else:
        dysgraphia_band = "High Risk"
        dysgraphia_score = float(speed_decay_pct)

    # --- 4. Comorbidity Detection ---
    mod_plus_count = sum(1 for band in [dyslexia_band, dyscalculia_band, dysgraphia_band] if band in ["Moderate Risk", "High Risk"])
    comorbidity_flag = mod_plus_count >= 2

    return {
        "tier": 2,
        "age_group": "Ages 6-9 (Manifestation Screening)",
        "branches": {
            "dyslexia": {
                "risk_band": dyslexia_band,
                "composite_score": round(dyslexia_score, 1),
                "comprehension_acc": round(comp_acc, 1),
                "spelling_acc": round(spelling_acc, 1),
                "ran_total_sec": round(ran_sec, 2),
                "dsm_icd": DSM_ICD_MAPPING["dyslexia"]
            },
            "dyscalculia": {
                "risk_band": dyscalculia_band,
                "composite_score": round(dyscalculia_score, 1),
                "magnitude_acc": round(mag_acc, 1),
                "fact_calc_delays": fact_calc_delay_count,
                "sequence_acc": round(seq_acc, 1),
                "dsm_icd": DSM_ICD_MAPPING["dyscalculia"]
            },
            "dysgraphia": {
                "risk_band": dysgraphia_band,
                "composite_score": round(dysgraphia_score, 1),
                "pause_ratio": round(pause_ratio, 2),
                "speed_decay_pct": round(speed_decay_pct, 1),
                "dsm_icd": DSM_ICD_MAPPING["dysgraphia"]
            }
        },
        "comorbidity_flag": comorbidity_flag,
        "comorbidity_details": "Comorbid SLD pattern detected across 2 or more cognitive branches (Dyslexia, Dyscalculia, or Dysgraphia)." if comorbidity_flag else "No multi-branch comorbidity detected.",
        "explainability": [
            f"Dyslexia Branch: {dyslexia_band} (Comprehension: {comp_acc:.1f}%, Spelling: {spelling_acc:.1f}%).",
            f"Dyscalculia Branch: {dyscalculia_band} (Accuracy: {avg_math_acc:.1f}%, Fact calculation delays: {fact_calc_delay_count}).",
            f"Dysgraphia Branch: {dysgraphia_band} (Graphomotor sentence drawing stability within normal limits)."
        ]
    }


# ── TIER 3 EVALUATION ENGINE (Ages 10-13: Compensation-Resistant) ──
def analyze_tier3_data(ran_multi_round, adaptive_decoding, sight_word_decay, long_comprehension, dyscalculia_t3, dysgraphia_t3):
    """
    Evaluates Tier 3 Compensation-Resistant Screening.
    100% accuracy across subtests yields Low Risk.
    """
    # 1. Multi-Round RAN
    r1_sec = float(ran_multi_round.get('round1_colors_sec', 12.0))
    r3_sec = float(ran_multi_round.get('round3_mixed_sec', 15.0))
    slowdown_pct = float(max(0.0, ((r3_sec - r1_sec) / max(1.0, r1_sec)) * 100.0))

    # 2. Adaptive Decoding Ceiling
    max_level_cleared = int(adaptive_decoding.get('max_level_cleared', 3))

    # 3. Sight-Word Decay Accuracy
    swd_correct = float(sight_word_decay.get('correct_count', 2))
    swd_total = float(max(1, sight_word_decay.get('total_count', 2)))
    swd_acc = (swd_correct / swd_total) * 100.0

    # 4. Long Reading Comprehension
    long_comp_acc = float(long_comprehension.get('accuracy', 100.0))

    avg_t3_acc = (long_comp_acc + swd_acc) / 2.0

    if avg_t3_acc >= 85.0 and max_level_cleared >= 2:
        d_band = "Low Risk"
        t3_dyslexia_score = float(max(0.0, 100.0 - avg_t3_acc))
    elif avg_t3_acc >= 60.0:
        d_band = "Moderate Risk"
        t3_dyslexia_score = float(100.0 - avg_t3_acc)
    else:
        d_band = "High Risk"
        t3_dyslexia_score = float(100.0 - avg_t3_acc)

    c_score = float(dyscalculia_t3.get('score', 0.0))
    c_band = "High Risk" if c_score >= 55.0 else ("Moderate Risk" if c_score >= 30.0 else "Low Risk")

    g_score = float(dysgraphia_t3.get('score', 0.0))
    g_band = "High Risk" if g_score >= 55.0 else ("Moderate Risk" if g_score >= 30.0 else "Low Risk")

    comorbidity_flag = sum(1 for b in [d_band, c_band, g_band] if b in ["Moderate Risk", "High Risk"]) >= 2

    return {
        "tier": 3,
        "age_group": "Ages 10-13 (Compensation-Resistant Screening)",
        "compensation_metrics": {
            "ran_slowdown_pct": round(slowdown_pct, 1),
            "adaptive_decoding_ceiling": f"Level {max_level_cleared} of 3",
            "sight_word_decay_error_pct": round(100.0 - swd_acc, 1),
            "long_comprehension_acc": round(long_comp_acc, 1)
        },
        "branches": {
            "dyslexia": {
                "risk_band": d_band,
                "composite_score": round(t3_dyslexia_score, 1),
                "dsm_icd": DSM_ICD_MAPPING["dyslexia"]
            },
            "dyscalculia": {
                "risk_band": c_band,
                "composite_score": round(c_score, 1),
                "dsm_icd": DSM_ICD_MAPPING["dyscalculia"]
            },
            "dysgraphia": {
                "risk_band": g_band,
                "composite_score": round(g_score, 1),
                "dsm_icd": DSM_ICD_MAPPING["dysgraphia"]
            }
        },
        "comorbidity_flag": comorbidity_flag,
        "explainability": [
            f"Dyslexia Branch: {d_band} (Decoding ceiling: Level {max_level_cleared}, Accuracy: {avg_t3_acc:.1f}%).",
            f"Sight-Word Decay: {100.0 - swd_acc:.1f}% error rate after distractor task.",
            f"Long Reading Comprehension: {long_comp_acc:.1f}% accuracy on reading-to-learn text."
        ]
    }


# ── TIER 4 EVALUATION ENGINE (Ages 14+: Executive Function + Academic Distress) ──
def analyze_tier4_data(distress_answers, t3_cognitive_data):
    """
    Evaluates Tier 4 Screening (Ages 14+).
    Combines Tier 3 cognitive assessment with Academic Task Distress Questionnaire.
    If cognitive accuracy is high (Low Risk), Social Masking is NOT flagged.
    """
    distress_total = 0
    domain_scores = {}
    for item_id, score_val in distress_answers.items():
        val = int(score_val)
        distress_total += val
        domain_scores[item_id] = val

    if distress_total >= 13:
        distress_band = "High Academic Distress"
    elif distress_total >= 7:
        distress_band = "Moderate Academic Distress"
    else:
        distress_band = "Low Academic Distress"

    t3_result = analyze_tier3_data(
        t3_cognitive_data.get('ran_multi_round', {}),
        t3_cognitive_data.get('adaptive_decoding', {}),
        t3_cognitive_data.get('sight_word_decay', {}),
        t3_cognitive_data.get('long_comprehension', {}),
        t3_cognitive_data.get('dyscalculia', {}),
        t3_cognitive_data.get('dysgraphia', {})
    )

    cog_high_mod = any(b['risk_band'] in ['Moderate Risk', 'High Risk'] for b in t3_result['branches'].values())

    social_masking_flag = False
    anxiety_discrepancy_flag = False
    masking_notes = ""

    if cog_high_mod and distress_band == "Low Academic Distress":
        social_masking_flag = True
        masking_notes = "⚠️ Social Masking Detected: Objective cognitive subtests reveal significant SLD risk, but adolescent self-reports minimal task distress."
    elif (not cog_high_mod) and distress_band == "High Academic Distress":
        anxiety_discrepancy_flag = True
        masking_notes = "ℹ️ Academic Distress Discrepancy: High self-reported task anxiety, but objective cognitive performance is within normal limits."
    elif (not cog_high_mod) and distress_band == "Low Academic Distress":
        masking_notes = "✓ Normal & Low Risk: Cognitive performance is within normal limits and aligns with low self-reported task distress."
    else:
        masking_notes = "✓ Consistent Assessment: Objective cognitive risk aligns with self-reported academic task distress."


    return {
        "tier": 4,
        "age_group": "Ages 14+ (Executive Function & Academic Distress Screening)",
        "academic_distress": {
            "total_score": distress_total,
            "max_score": 20,
            "distress_band": distress_band,
            "domain_scores": domain_scores,
            "dsm_icd": DSM_ICD_MAPPING["academic_distress"]
        },
        "cognitive_assessment": t3_result,
        "social_masking_detected": social_masking_flag,
        "anxiety_discrepancy_detected": anxiety_discrepancy_flag,
        "masking_analysis": masking_notes,
        "explainability": [
            f"Academic Task Distress: {distress_band} ({distress_total}/20 score).",
            masking_notes,
            f"Cognitive Battery: Dyslexia ({t3_result['branches']['dyslexia']['risk_band']}), Dyscalculia ({t3_result['branches']['dyscalculia']['risk_band']}), Dysgraphia ({t3_result['branches']['dysgraphia']['risk_band']})."
        ]
    }
