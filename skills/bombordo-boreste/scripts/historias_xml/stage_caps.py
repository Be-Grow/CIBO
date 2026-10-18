"""Legenda animada (faixa colorida + matte) e eventos de punch-in de uma história.
  cd <historia> && python3 ../stage_caps.py <clip>"""
import os, sys, json, copy
SK = os.path.expanduser('~/.claude/skills/bombordo-boreste/scripts')
sys.path.insert(0, SK); sys.path.insert(0, os.path.join(SK, 'kinetic'))
import kinrender
from common import load_config

clip = sys.argv[1]
cfg = load_config(clip, 'kinetic.yaml')
blocks = json.load(open(f'kinetic/blocks_{clip}.json'))
TOTAL = json.load(open('edit.json'))['total']
bl = copy.deepcopy([b for b in blocks['blocks'] if b['words']])
kinrender.timeline(bl, cfg, 9999)
pc = cfg['punch_in']
c = dict(impact_pulses=[dict(t=round(max(0.3, b['t_in']), 3), amount=pc['amount'], until=round(b['t_out'], 3))
                        for b in bl if b['kind'] == 'highlight'],
         punch={k: pc[k] for k in ('ramp', 'bezier', 'subframes', 'shutter', 'min_hold', 'min_rest')})
json.dump(c, open('punch_events.json', 'w'), indent=1)
print('punch', len(c['impact_pulses']), 'band', cfg['position']['band_height'], flush=True)
kinrender.render(copy.deepcopy(blocks), cfg, TOTAL, 'caps')
print('caps ok', flush=True)
