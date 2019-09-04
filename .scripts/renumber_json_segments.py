import json
import pathlib
segment_id_mapping = json.load(open('segment_id_mapping.json'))

files = sorted(pathlib.Path('../').glob('[a-z]*/**/*.json'))

for file in files:

    with file.open('r') as f:
        data = json.load(f)
    
    new_data = {}
    for key, value in data.items():
        if key in segment_id_mapping:
            key = segment_id_mapping[key][-1]
        new_data[key] = value
    

    with file.open('w') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
