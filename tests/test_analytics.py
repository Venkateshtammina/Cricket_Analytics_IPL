import pytest
import numpy as np

# A lightweight mock version of your app logic to verify boundary math without pulling live DB hits during testing
def calculate_live_win_percentage_mock(balls_left, wickets_lost, current_score, target_score):
    runs_needed = target_score - current_score
    if runs_needed <= 0: return 100.0
    if balls_left <= 0: return 0.0
    if wickets_lost >= 10: return 0.0
    
    wickets_left = 10 - wickets_lost
    resource_multiplier = (wickets_left / 10.0) ** 0.45
    
    req_run_rate = (runs_needed / balls_left) * 6
    pressure_index = req_run_rate / (6.0 * ((wickets_left / 10.0) + 0.15))
    win_prob = 100.0 / (1.0 + np.exp(2.2 * (pressure_index - 1.05)))
    
    return max(min(win_prob * resource_multiplier, 98.0), 2.0)

def test_win_percentage_boundaries():
    assert calculate_live_win_percentage_mock(30, 3, 170, 160) == 100.0
    assert calculate_live_win_percentage_mock(0, 3, 120, 160) == 0.0
    assert calculate_live_win_percentage_mock(30, 10, 120, 160) == 0.0

def test_wicket_drop_sensitivity():
    prob_dominant = calculate_live_win_percentage_mock(30, 3, 120, 160)
    prob_collapse = calculate_live_win_percentage_mock(30, 7, 120, 160)
    assert prob_dominant > prob_collapse