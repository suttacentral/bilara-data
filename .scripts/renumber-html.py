import json
import regex
import pathlib
from itertools import zip_longest
from tempfile import NamedTemporaryFile
from collections import defaultdict

import lxml.html

from common import bilarasortkey


        


def iter_segments(root):
    for element in root.cssselect('a[data-uid]'):
        segment_id = element.get('data-uid')
        if ':' not in segment_id:
            print(f'Malformed segment_id: {segment_id}')
            continue
        yield element

def renumber_zeros(root):
    i = 1
    for element in iter_segments(root):
        segment_id = element.get('data-uid')
        uid, num = segment_id.split(':')
        
        if num.startswith('0'):
            element.set('data-uid', f'{uid}:0.{i}')
            i += 1
        else:
            return i > 1



        
def renumber_segments(root, segment_id_mapping, problems):
    segments = root.cssselect('a[data-uid]')

    for i, segment in enumerate(segments):
        segment_id = segment.get('data-uid')

        uid, nums = segment_id.split(':')

        if nums.startswith('0.'):
            for e in segment.iterancestors():
                if e.tag == 'header':
                    break
                else:
                    problems.append('segment_id starts with 0 but is not in header')
        



def renumber_segments(root, segment_id_mapping):
    changed = False
    last_nums = None
    for element in iter_segments(root):
        segment_id = element.get('data-uid')
        uid, num = element.get('data-uid').split(':')
        
        
        nums = num.split('.')
        
        if last_nums and len(last_nums) in {2, 3} and len(last_nums) == len(nums):
            should_be_1 = False

            if nums[:-1] == last_nums[:-1]:
                m = regex.match(r'(\d+)([a-z]*)', last_nums[-1])
                last_num, last_alpha = m[1], m[2]
                m = regex.match(r'(\d+)([a-z]*)', nums[-1])
                num, alpha = m[1], m[2]

                if alpha:
                    continue
                if should_be_1:
                    new_num = '1'
                else:
                    new_num = str(int(last_num) + 1)
                if new_num != nums[-1]:
                    nums[-1] = new_num
                    new_segment_id = f'{uid}:{".".join(nums)}'
                    if segment_id != new_segment_id:
                        print(f'Replace: {segment_id} -> {new_segment_id}')
                        element.set('data-uid', new_segment_id)
                        segment_id_mapping[segment_id].append(new_segment_id)
                        changed = True
        last_nums = nums
    return changed
            
            
            
            
problems = {}

def compare_order(a, b):
    nums_a = [l[1] for l in a]
    nums_b = [l[1] for l in b]
    if nums_a == nums_b:
        return False
    problems[a[0][0]] = (nums_a, nums_b)
    for i, j in zip(nums_a, nums_b):
        if i != j:
            print(f'{a[0][0]}: Sort Mismatch {i} != {j}')
            return



def check_ordering(segment_ids, file):
    
    compare_order(segment_ids, sorted(segment_ids, key=bilarasortkey))
    compare_order(segment_ids, sorted(reversed(segment_ids), key=bilarasortkey))
    

def compare_strings(a, b, pattern, file):
    strings = []
    a_strings = a.split('\n')
    b_strings = b.split('\n')
    for i, (a_s, b_s) in enumerate(zip_longest(a_strings, b_strings)):
        a_m = regex.search(pattern, a)
        b_m = regex.search(pattern, b)
        
        strings.append((i, a_m[0] if a_m else None, b_m[0] if b_m else None))
    
    for lineno, a_s, b_s in strings:
        if a_s != b_s:
            print(f'{file.name}:{lineno}: Mismatch {a_s}, {b_s}')
            return False
    return True
        
segment_id_mapping = defaultdict(list)

noact = False
HTML_DIR = pathlib.Path('./html')
for file in sorted(HTML_DIR.glob('**/*.html')):
    print(f'Processing {str(file)}')
    with file.open('r') as f:
        original_string = f.read()
    root = lxml.html.fromstring(original_string)

    changed = False
    
    
    changed = renumber_segments(root, segment_id_mapping) or changed 
    
    seen = set()

    segment_ids = []
    for element in iter_segments(root):
        segment_id = element.get('data-uid')
        if segment_id in seen:
            print(f'{uid} is not unqiue')
        uid, num = segment_id.split(':')
        segment_ids.append((uid, num))
    
    
    check_ordering(segment_ids, file)
    
    file_uid = regex.sub(r'(\D)(0+)', r'\1', file.stem)
    nums = []
    last_nums = None
    for uid, segment_id in segment_ids:
        if file_uid != uid:
            print(f'Mismatched UID: {uid} in {file_uid}')
    
    if not noact and changed:
        with file.open('w') as f:
            f.write(lxml.html.tostring(root, encoding='unicode'))

with open('segment_id_mapping.json', 'w') as f:
    json.dump(segment_id_mapping, f, indent=2)