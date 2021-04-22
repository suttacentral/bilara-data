import json
import regex
import pathlib

from common import repo_dir
from collections import defaultdict

sc_locale_dir = pathlib.Path('../../suttacentral/client/localization/elements/').resolve()

out_folder = pathlib.Path('./locale/')

def path_to_key(path):
    name = path.stem.split('_')[0]
    if 'static-page' in path.parts:
        name = 'static-' + name + '-page'
    elif 'sc-page' in path.parts:
        name = 'sc-' + name + '-page'


en_data = {}
en_stems = set()
en_count = 0
for file in repo_dir.glob('root/en/site/**/*.json'):
    with file.open() as f:
        data = json.load(f)
    en_stems.add(file.stem.split('_')[0])
    en_count += len(data)
    en_data[path_to_key(file)] = data
    
for lang_folder in repo_dir.glob('translation/*'):
    locale_files = [f for f in lang_folder.glob('site/**/*.json') if f.stem.split('_')[0] in en_stems]
    if not locale_files:
        continue
    

    lang_data = {}
    lang_count = 0
    for file in locale_files:
        with file.open() as f:
            data = json.load(f)
        lang_data[path_to_key(file)] = data
        lang_count += len(data)
    
    completion = lang_count / en_count
    print(lang_folder.stem, completion)


    