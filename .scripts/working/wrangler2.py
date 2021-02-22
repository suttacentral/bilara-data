import json
import regex
import pathlib
from Levenshtein import jaro_winkler
import sys
sys.path.append('..')
import align
from common import bilarasortkey, repo_dir



root_file_mapping = {}

out_dir = pathlib.Path('./pt')
lost_dir = pathlib.Path('./lost')

for file in (repo_dir / 'root/pli/ms').glob('**/*.json'):
    uid, _ = file.stem.split('_')

    root_file_mapping[uid] = file


def align_pt(current, stale):


    return result

def normalize(s):
    s = s.replace('ṁ', 'ṃ')
    s = s.replace('ṅ', 'ṃ')
    s = s.strip()
    s = s.casefold()
    s = regex.sub(r'[^\p{alpha}\s]', '', s)
    s = regex.sub(r'\s+', r'', s)
    return s

new_files = sorted(pathlib.Path('out').glob('**/?n/*.json'), key=bilarasortkey)

key_mapping = {}

okay = 0
not_okay = 0

out_dir = pathlib.Path('translation/pt/laera-quaresma/')
problems = []
for file in new_files:
    print(f'\n{str(file)}')
    uid = file.stem

    if uid not in root_file_mapping:
        print(f'{uid} not found in root files')
        continue
    
    root_file = root_file_mapping[uid]

    out_folder = out_dir / '/'.join(root_file.relative_to(repo_dir).parts[3:-1])

    if not out_folder.exists():
        out_folder.mkdir(parents=True)

    file_uid = root_file.stem.split('_')[0]
    out_file = out_folder / f'{file_uid}_translation-pt-laera-quaresma.json'
    if out_file.exists():
        continue
    
    current_root_data = [(v, k) for k,v in json.load(root_file.open()).items()]
    stale_data = [(v['pli'], k, v['pt']) for k, v in json.load(file.open()).items()]

    aligned_data = align.align(current_root_data, stale_data)

    fixed_data = {}
    missed_data = []

    perfect = True

    for i, (root, stale) in enumerate(aligned_data):
        
        if not stale:
            stale = (None, None, None)
        
        stale_root_string, stale_uid, pt_string = stale

        if not pt_string:
            continue
            
        if root:
            root_string, root_uid = root

            sim = jaro_winkler(normalize(root_string), normalize(stale_root_string))
            if sim < 0.95:
                perfect = False
                print('RSC: ' + root_string)
                print('     ' + stale_root_string)
                pt_string = '!!! ' + pt_string
            
            fixed_data[root_uid] = pt_string
        elif pt_string and not pt_string.isspace():
            missed_data.append( (i, stale) )
    
    if missed_data:
        resolved_count = 0
        for i, (root_string, uid, pt_string) in missed_data:
            resolved = False
            if not root_string:
                continue
            prev = aligned_data[i - 1][0]
            if prev:
                prev_root_string, prev_root_uid = prev
                if normalize(root_string) in normalize(prev_root_string):
                    if prev_root_uid in fixed_data:
                        fixed_data[prev_root_uid] += ' || ' + pt_string
                    else:
                        fixed_data[prev_root_uid]  = '|| ' + pt_string
                    resolved = True
            if not resolved:
                next = aligned_data[i + 1][0]
                if next:
                    next_root_string, next_root_uid = next
                    if normalize(root_string) in normalize(next_root_string):
                        fixed_data[next_root_uid] = pt_string + ' || ' + fixed_data[next_root_uid]
                    else:
                        fixed_data[next_root_uid] = '|| ' + pt_string
                    resolved = True
            
            if resolved:
                resolved_count += 1
        if resolved_count == len(missed_data):
            print('    All alignment issues resolved automatically.')


    
    with out_file.open('w') as f:
        json.dump(fixed_data, f, indent=2, ensure_ascii=False, sort_keys=bilarasortkey)
    
    
    





def old_code():
    root_strings = {normalize(v):  k for k,v in root_data.items()}
    same_length = len(root_data) == len(new_data)
    problem = False
    fixed_data = {}
    if same_length:
        for k, v in new_data.items():
            
            for root_k, new_k in zip(root_data, new_data):
                if normalize(root_data[root_k]) != normalize(new_data[new_k]['pli']):
                    print('Root string does not match: ')
                    print(f'   ' + root_data[root_k])
                    print(f'   ' + new_data[new_k]['pli'])
                fixed_data[root_k] = new_data[new_k]
    
    if not same_length:
        not_found = 0
        for d in new_data.values():
            if normalize(d['pli']) not in root_strings:
                not_found += 1
        print(f'Problem with {uid} (length difference of {len(root_data) - len(new_data)}, {not_found})')
        
                #print(f"  {d['pli']} not found")

        if not same_length and 'an' in uid:
            not_okay += 1
            #print('\n'.join(unified_diff(
                #[normalize(s) for s in root_data.values()],
                #[normalize(d['pli']) for d in new_data.values()])))
            #print('\n'.join(unified_diff(list(root_data), list(new_data))))
    else:
        print(uid)
        okay += 1

    
            