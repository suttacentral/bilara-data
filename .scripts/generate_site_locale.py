import pathlib
import json
import regex

from inflection import camelize
from common import repo_dir
from collections import defaultdict
from common import bilarasortkey

sc_locale_dir = pathlib.Path('../../suttacentral/client/localization/elements/').resolve()

folders = [sc_locale_dir] + list(sc_locale_dir.glob('*'))


def simplify_name(filename):
    return regex.search(r'^(?:sc-|static_)?(.+?)(?:-page)?$', filename)[1]


def sort_key(file):
    if file.stem == 'en':
        return ''
    else:
        return file.stem

renames = {
    'action-items': 'action',
    'donate-now': 'donate',
    'donation-success': 'donate',
    'error-icon': 'error',
    'language-base-menu': 'menu',
    'linden-leaves': 'menu',
    'more-menu': 'menu',
    'navigation-menu': 'navigation',
    'page-dictionary': 'dictionary',
    'page-search': 'search',
    'page-selector': 'selector',
    'parallel-list': 'parallel',
    'parallel-item': 'parallel',
    'search-filter-menu': 'search',
    'site-layout': 'layout',
    'static-page-selector': 'selector',
    'suttaplex-share-menu': 'share',
    'text-carousel': 'text',
    'top-sheet': 'dictionary',
    'universal-action-items': 'search',
    
    'useoffline': 'useOffline',
    'name (optional)': 'nameOptional',
    
    'suttaplex:networkError': 'error:networkError',
    'text:error404': 'error:error404'
    
}
seen = set()
non_renamed = set()

# Three data sources:
# 
# * Current translations
# * SuttaCentral client code


transformation_mapping = {}
def make_key(base_name, k):
    new_k = k
    if new_k.isupper():
        new_k = new_k.casefold()
    new_k = camelize(new_k.replace('-', '_'), uppercase_first_letter=False)
    if new_k in renames:
        new_k = renames[new_k]
    seen.add(k)
    
    if base_name in renames:
        base_name = renames[base_name]
    key = f'{base_name}:{new_k}'
    if key in renames:
        key = renames[key]
    else:
        non_renamed.add(base_name)
    transformation_mapping[(base_name, k)] = key
    return key

def json_dump(data, f):
    if isinstance(data, dict):
        data = dict(sorted(data.items(), key=bilarasortkey))
    json.dump(data, f, ensure_ascii=False, indent=2)

bad = {}
global_data = defaultdict(dict)
for i, folder in enumerate(folders):
    base_name = simplify_name(folder.name)
    
    merged_data = defaultdict(dict)
    for language_file in sorted(folder.glob('*.json'), key=sort_key):
        language_uid = language_file.stem
        with language_file.open('r') as f:
            data = json.load(f)[language_uid]
        
        for k, v in data.items():
            if language_uid != 'en':
                if k not in merged_data:
                    bad[language_file] = (k,v)
                    continue
            merged_data[k][language_uid] = v
    
    if folder.name.startswith('static_'):
        merged_data = {
            str(i) : v 
            for i, v
            in enumerate(merged_data.values(), 1)
        }

    #Rekey

    merged_data = {make_key(base_name, k): v for k,v in merged_data.items()}

    split_data = defaultdict(dict)

    for k, v in merged_data.items():
        for language_uid, string in v.items():
            if string:
                split_data[language_uid][k] = string

    for language_uid, data in split_data.items():
        if not data:
            continue
        is_interface = not folder.parent.name == 'static-page'
        if language_uid == 'en':
            out_dir = repo_dir / 'root' / 'en' / 'site'
            new_name =  base_name + '_root-en-site'
        else:
            out_dir = repo_dir / 'translation' / language_uid / 'site'
            new_name =  base_name + f'_translation-{language_uid}-site'
        if not out_dir.exists():
                out_dir.mkdir(parents=True)
        if folder.name.startswith('static_'):
            out_file = (out_dir / new_name).with_suffix('.json')
            # with out_file.open('w') as f:
            #     json_dump(data, f)
        elif is_interface:
            global_data[language_uid].update(data)
            if i == len(folders) - 1:
                out_file = out_dir / 'interface.json'
                # with out_file.open('w') as f:
                #     json_dump(global_data[language_uid], f)
        


found = {}
interface_data = defaultdict(dict)
dry = False
existing_folders = [repo_dir / 'root/en/site', *(repo_dir.glob('translation/**/site'))]

l_renames = defaultdict(dict)

for folder in existing_folders:
    lang_uid = folder.relative_to(repo_dir).parts[1]
    for file in folder.glob('**/*.json'):
        if 'name' in file.parts:
            continue
        if file.name == 'interface.json':
            file.unlink()

        
        suffix = file.name.split('_')[1]
        
        with file.open() as f:
            data = json.load(f)
        is_interface = False
        
        new_data = {}
        for k, v in data.items():
            new_key = make_key(*k.split(':'))
            if not k[-1].isdigit():
                l_renames[lang_uid][k] = new_key
            if new_key in global_data['en']:
                found[new_key] = file
                is_interface = True
                interface_data[lang_uid][new_key] = v
            else:
                new_data[new_key] = v
        if not is_interface:
            out_file = folder / f'{new_key.split(":")[0]}_{suffix}'
            if not dry:
                with out_file.open('w') as f:
                    json_dump(new_data, f)
        if not dry:
            file.unlink()
    interface_file = folder / f'interface_{suffix}'
    if not dry:
        with interface_file.open('w') as f:
            json_dump(interface_data[lang_uid], f)