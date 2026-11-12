#!/usr/bin/env python3
"""sweep_print.py: print the summary of a sweep_<name>.json, short. sim pass only."""
import json
import sys
d = json.load(open(sys.argv[1]))
KEYS = ('n', 'falls', 'falls_by_stage', 'not_across', 'runs_steering_on_edge', 'stage_turn_moves_mean', 'stage_toe_gap_mm', 'turn_spot_err_x_mm', 'turn_spot_err_y_mm',
        'turn_spot_err_rms_mm', 'turn_spot_err_max_mm', 'fine_rounds_mean', 'time_to_turn_start_s', 'edge_cross_s')
for s in d['summary']:
    print(s['setting'])
    for k in ('6.0 V', '7.2 V', 'the 29 that fell before'):
        r = s['result'][k]
        if r['n']:
            print('   ', k, {a: r[a] for a in KEYS})
