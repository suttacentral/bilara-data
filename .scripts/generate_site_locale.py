import pathlib
import json
import regex

from common import repo_dir
from collections import defaultdict

sc_locale_dir = pathlib.Path('../../suttacentral/client/localization/elements/').resolve()

folders = sc_locale_dir.glob('*')



def simplify_name(filename):
    return regex.search(r'^(?:sc-|static_)?(.+?)(?:-page)?$', filename)[1]


def sort_key(file):
    if file.stem == 'en':
        return ''
    else:
        return file.stem
    
for folder in folders:
    base_name = simplify_name(folder.name)
    
    merged_data = defaultdict(dict)
    for language_file in sorted(folder.glob('*.json'), key=sort_key):
        language_uid = language_file.stem
        with language_file.open('r') as f:
            data = json.load(f)[language_uid]
        
        for k, v in data.items():
            merged_data[k][language_uid] = v
    
    if folder.name.startswith('static_'):
        merged_data = {
            str(i) : v 
            for i, v
            in enumerate(merged_data.values(), 1)
        }

    #Rekey

    merged_data = {f'{base_name}:{k}': v for k,v in merged_data.items()}

    split_data = defaultdict(dict)

    for k, v in merged_data.items():
        for language_uid, string in v.items():
            if string:
                split_data[language_uid][k] = string

    for language_uid, data in split_data.items():
        if not data:
            continue
        if language_uid == 'en':
            out_dir = repo_dir / 'root' / 'en' / 'site'
            new_name =  base_name + '_root-en-site'
        else:
            out_dir = repo_dir / 'translation' / language_uid / 'site'
            new_name =  base_name + f'_translation-{language_uid}-site'
        print(new_name)
        if folder.name.startswith('static_'):
            out_dir = out_dir / 'static-page'
        elif folder.name.startswith('sc-'):
            out_dir = out_dir / 'sc-page'
        if not out_dir.exists():
            out_dir.mkdir(parents=True)
        out_file = (out_dir / new_name).with_suffix('.json')
        with out_file.open('w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

         