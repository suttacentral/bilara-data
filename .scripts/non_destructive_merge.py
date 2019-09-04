import json
import pathlib

old_files = sorted(pathlib.Path('../').glob('[a-z]*/**/*.json'))

new_files = {
    file.name: file
    for file in
    pathlib.Path('./json-out').glob('**/*.json')
}

for file in old_files:

    if file.name not in new_files:
        continue

    with file.open('r') as f:
        old_data = json.load(f)
    
    with new_files[file.name].open('r') as f:
        new_data = json.load(f)
    
    
    
    merged_data = {}
    for key, value in new_data.items():
        if key in old_data:
            merged_data[key] = old_data[key]
        else:
            merged_data[key] = new_data[key]

    with file.open('w') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
