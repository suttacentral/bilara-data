import json
import regex
import pathlib
from itertools import groupby
import sys
sys.path.append('..')
from common import bilarasortkey

with open('pootle_dump.json') as f:
    data = json.load(f)

def fix_name(s):
    s = unzfill(s)
    s = s.replace('pi-', 'pli-')
    return s

def unzfill(s):
    return regex.sub(r'([a-z]|\b)0+', r'\1', s)

data = list(data.values())[0]

out_dir = pathlib.Path('./out')

for entry in data:
    if not entry['context']:
        print(entry)

for path, group in groupby(data, key=lambda d: d['pootle_path']):
    if 'info.po' in path:
        continue
    group = list(group)
    try:
        entries = sorted(group, key=lambda d: bilarasortkey(str(d['context'])))
    except TypeError:
        entries = group
    

    out_file = (out_dir / fix_name(path[1:])).with_suffix('.json')

    new_data = {d['context']: {'pli': d['source_f'], 'pt': d['target_f']} for d in entries if d['target_f'] }
   
    if not new_data:
        continue

    if not any(regex.search(r'\p{alpha}', d['pt']) for d in new_data.values()):
        continue

    if not out_file.parent.exists():
        out_file.parent.mkdir(parents=True)

    with out_file.open('w') as f:
        print(f'Writing {len(new_data)} entries to {out_file}')
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    

        
    

    
    

    
        
