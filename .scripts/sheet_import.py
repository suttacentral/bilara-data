#!/usr/bin/env python3

import logging
import json
import argparse
import pyexcel
import regex
import sys
import pathlib
import yaml

from itertools import groupby
from common import iter_json_files, repo_dir, bilarasortkey

def check_segment_id(segment_id, file):
    if segment_id.count(':') != 1:
        logging.error(f'Segment ID "{segment_id}" in "{str(file)} is malformed, expected a single ":", but {segment_id.count(":")} found')
        return False
    return True

def load_paths_file(paths_file):
    paths, muids_mapping = None, None
    with open(paths_file, 'r', encoding='utf-8') as f:
        data = yaml.load(f)
        print(data)
        if 'PATHS' in data:
            paths = {k: repo_dir / v  for k,v in data['PATHS'].items()}
        if 'MUIDS' in data:
            muids_mapping = data['MUIDS']
    
    return paths, muids_mapping

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Import Spreadsheet")
    parser.add_argument('file', help='Spreadsheet file to import. CSV, TSV, ODS, XLS')
    parser.add_argument('-p', '--paths-file', help='.yaml file describing how to generate paths')
    parser.add_argument('-q', '--quiet', help='Do not display changes to files')
    parser.add_argument('--update', help="Instead of overwriting files, just update entries")
    args = parser.parse_args()

    paths = None
    muids_mapping = None
    if args.paths_file:
        paths, muids_mapping = load_paths_file(args.paths_file)
        
    
    print(paths)
    print(muids_mapping)

    rows = pyexcel.iget_records(file_name=args.file)
    
    files = {file.stem: file for file in iter_json_files()}

    segment_uid_to_file_mapping = {}

    if not paths:

        file_uid = pathlib.Path(args.file).stem

        def get_file(uid, file_uid, muids):
            filestem = f'{uid}_{muids}'
            if filestem in files:
                return files[filestem]
            
            alt_filestem = f'{file_uid}_{muids}'
            if alt_filestem in files:
                return files[alt_filestem]

            uid_stem = regex.match(r'[a-z]+(\d+\.)?', uid)[0]

            rex = regex.compile(f'{regex.escape(uid_stem)}.*_{muids}')

            if muids not in segment_uid_to_file_mapping:
                segment_uid_to_file_mapping[muids] = {}

            for i in range(0, 2):
                file = segment_uid_to_file_mapping[muids].get(uid)
                if file:
                    return file
                if i > 0:
                    break

                for filestem, file in files.items():
                    if rex.fullmatch(filestem):
                        with file.open('r') as f:
                            data = json.load(f)
                        for segment_id in data:
                            if check_segment_id(segment_id, file):
                                segment_uid = segment_id.split(':')[0]
                                segment_uid_to_file_mapping[muids][segment_uid] = file
            
            raise ValueError('Could not find file for {}_{}'.format(uid, muids))

    errors = 0

    files_erased = set()
    
    for uid, group in groupby(rows, lambda row: row['segment_id'].split(':')[0]):
        group = list(group)
        fields = [k for k in group[0].keys() if k not in {'segment_id', 'old_uid', 'new_uid'}]
        data = {field: {} for field in fields}
        
        for record in group:
            segment_id = record['segment_id']
            if not segment_id:
                continue
            if not check_segment_id(segment_id, args.file):
                errors += 1
                continue
            for field in fields:
                value = record[field]
                if value:
                    data[field][segment_id] = value
        
        for field in fields:
            if not data[field]:
                continue
            if paths:
                if field in paths:
                    if muids_mapping and field in muids_mapping:
                        muids = muids_mapping[field]
                    else:
                        muids = field
                    file = paths[field] / f'{uid}_{muids}.json'
                
                else:
                    print(f'ERROR: Could not find field "{field}" in {args.paths_file}')
                    errors += 1
            else:
                file = get_file(uid=uid, file_uid=file_uid, muids=field)
                if not file:
                    print('ERROR: Could not find file for {}_{}'.format(uid, field), file=sys.stderr)
                    errors += 1
                    continue
            
            if args.update or file in files_erased and file.exists():
                with file.open('r') as f:
                    old_data = json.load(f)
            else:
                old_data = {}
                if file.exists():
                    files_erased.add(file)
        
            merged_data = {}

            segment_ids = sorted(set(old_data) | set(data[field]), key=bilarasortkey)

            for segment_id in segment_ids:
                old_value = old_data.get(segment_id)
                if not old_value:
                    # Maybe do something here
                    pass
                value = data[field].get(segment_id)
                if value is None:
                    # Doesn't exist in spreadsheet
                    value = old_value
                value = str(value) if isinstance(value, int) else value
                old_value = str(old_value) if isinstance(value, int) else old_value
                if not args.quiet and old_value != value:
                    print('{uid}_{field}:{segment_id}: {old_value} -> {value}'.format(**locals()))
                merged_data[segment_id] = value
            if paths:
                if not file.parent.exists():
                    file.parent.mkdir(parents=True)
            with file.open('w') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)
    if errors > 0:
        print(f'{errors} occured while importing sheet, not all data was imported', file=sys.stderr)
        exit(1)
    exit(0)