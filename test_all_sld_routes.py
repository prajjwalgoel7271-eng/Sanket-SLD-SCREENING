import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app

def run_tests():
    print("==================================================")
    print("    SANKET ALL 13 LANGUAGES TEST SUITE (1-4)     ")
    print("==================================================")

    client = app.test_client()

    all_13_langs = ['en', 'hi', 'bn', 'mr', 'ta', 'te', 'gu', 'kn', 'ml', 'pa', 'or', 'ur', 'bho']

    # 1. Test Content API across ALL 13 regional languages for all 4 Tiers
    for t in [1, 2, 3, 4]:
        for lang in all_13_langs:
            res = client.get(f'/api/sld/content/{t}?lang={lang}')
            assert res.status_code == 200, f"Failed Content API Tier {t} ({lang})"
            data = res.get_json()
            assert 'content' in data, f"Missing content key in Tier {t} ({lang})"
            assert data.get('fallback') == False, f"Unexpected fallback to English for lang={lang} Tier {t}"
            print(f"[Content Bank OK] Tier {t} ({lang.upper()}): Loaded native localized content without fallback.")

    # 2. Test Tier 1 Analysis API
    t1_payload = {
        "rhyme_results": [{"correct": True, "time_sec": 1.5}, {"correct": True, "time_sec": 1.8}, {"correct": True, "time_sec": 1.6}],
        "subitizing_results": [{"correct": True, "time_sec": 1.1}, {"correct": True, "time_sec": 1.1}],
        "motor_results": {"path_deviation_px": 5.0, "midline_pause_sec": 0.2, "completion_time_sec": 4.0}
    }
    t1_res = client.post('/api/sld/analyze/tier1', data=json.dumps(t1_payload), content_type='application/json')
    assert t1_res.status_code == 200, "Tier 1 Analysis Failed"
    t1_json = t1_res.get_json()
    assert t1_json['domain_results']['phonological_precursor']['risk_band'] == 'Low Risk'
    print("[OK] Tier 1 outputs LOW RISK for 100% accuracy!")

    # 3. Test Tier 2 Analysis API
    t2_payload = {
        "dyslexia": {"comprehension_acc": 100.0, "spelling_acc": 100.0, "decoding_accuracy": 100.0, "ran_total_sec": 12.0},
        "dyscalculia": {"magnitude_accuracy": 100.0, "fact_accuracy": 100.0, "sequence_accuracy": 100.0, "fact_calculation_delays": 0},
        "dysgraphia": {"pause_duration_ratio": 0.10, "speed_decay_pct": 10.0, "stroke_jitter_px": 0.0}
    }
    t2_res = client.post('/api/sld/analyze/tier2', data=json.dumps(t2_payload), content_type='application/json')
    assert t2_res.status_code == 200, "Tier 2 Analysis Failed"
    t2_json = t2_res.get_json()
    assert t2_json['branches']['dyslexia']['risk_band'] == 'Low Risk'
    assert t2_json['branches']['dyscalculia']['risk_band'] == 'Low Risk'
    assert t2_json['branches']['dysgraphia']['risk_band'] == 'Low Risk'
    print("[OK] Tier 2 evaluates Dyslexia, Dyscalculia, Dysgraphia branches as LOW RISK!")

    # 4. Test Tier 3 Analysis API
    t3_payload = {
        "ran_multi_round": {"round1_colors_sec": 12.0, "round3_mixed_sec": 13.0},
        "adaptive_decoding": {"max_level_cleared": 3},
        "sight_word_decay": {"correct_count": 2, "total_count": 2},
        "long_comprehension": {"accuracy": 100.0},
        "dyscalculia": {"score": 0.0},
        "dysgraphia": {"score": 0.0}
    }
    t3_res = client.post('/api/sld/analyze/tier3', data=json.dumps(t3_payload), content_type='application/json')
    assert t3_res.status_code == 200, "Tier 3 Analysis Failed"
    t3_json = t3_res.get_json()
    assert t3_json['branches']['dyslexia']['risk_band'] == 'Low Risk'
    print("[OK] Tier 3 evaluates 100% accuracy as LOW RISK!")

    # 5. Test Tier 4 Analysis API
    t4_payload = {
        "distress_answers": {"q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0, "q6": 0, "q7": 0, "q8": 0, "q9": 0, "q10": 0},
        "cognitive_data": t3_payload
    }
    t4_res = client.post('/api/sld/analyze/tier4', data=json.dumps(t4_payload), content_type='application/json')
    assert t4_res.status_code == 200, "Tier 4 Analysis Failed"
    t4_json = t4_res.get_json()
    assert t4_json['academic_distress']['distress_band'] == 'Low Academic Distress'
    assert t4_json['social_masking_detected'] == False
    print("[OK] Tier 4 correctly outputs LOW RISK & Social Masking FALSE!")

    # 6. Test Page Routes
    for route in ['/', '/about', '/disclaimer', '/test/sld', '/test/sld/tier1', '/test/sld/tier2', '/test/sld/tier3', '/test/sld/tier4', '/test/sld/results']:
        p_res = client.get(route)
        assert p_res.status_code == 200, f"Failed route {route}"
        print(f"[Page Route] {route}: 200 OK")

    print("\n==================================================")
    print(" [SUCCESS] ALL 13 LANGUAGES & TIERS (1-4) PASSED 100%! ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
