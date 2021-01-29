import pathlib
import json
import regex

from common import repo_dir

sc_locale_dir = pathlib.Path('/home/blake/programming/suttacentral/client/localization/elements/').resolve()

folders = sc_locale_dir.glob('*')

def simplify_name(filename):
    return regex.search(r'^(?:sc-|static_)?(.+?)(?:-page)?$', filename)[1]

for folder in folders:
    base_name = simplify_name(folder.name)
    
    
    for language_file in folder.glob('*.json'):
        language_uid = language_file.stem
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

        with language_file.open('r') as f:
            data = json.load(f)[language_uid]
        
        if folder.name.startswith('static_'):
            data = {
                str(i) : v 
                for i, v
                in enumerate(data.values(), 1)
            }
        
        with out_file.open('w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


         