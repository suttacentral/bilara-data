#!/usr/bin/env python3

import logging
import json
import argparse
import csv
import re
import sys
import pathlib


sys.path.append('..')

from itertools import groupby
from common import iter_json_files, repo_dir, bilarasortkey

def load_sheet(file):
    m = re.search(r'.*(\.\w+)$', file.name)
    if not m:
        suffix = '.csv'
    else:
        suffix = m[1]
    
    if suffix in {'.csv', '.tsv'}:
        dialect = {
            '.csv': csv.excel,
            '.tsv': csv.excel_tab
        }[suffix]

        with file.open('r', encoding='utf8') as f:
            reader = csv.DictReader(f, dialect=dialect)
            return list(reader)
    else:
        import pyexcel
        return pyexcel.iget_records(file_name=file.name)

def check_segment_id(segment_id, file):
    if segment_id.count(':') != 1:
        logging.error(f'Segment ID "{segment_id}" in "{str(file)} is malformed, expected a single ":", but {segment_id.count(":")} found')
        return False
    return True

def load_paths_file(paths_file):
    paths, muids_mapping = None, None
    with open(paths_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(data)
        if 'paths' in data:
            paths = {k: repo_dir / v  for k,v in data['paths'].items()}
        if 'muids' in data:
            muids_mapping = data['muids']
    
    return paths, muids_mapping

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Import Spreadsheet")
    parser.add_argument('file', help='Spreadsheet file to import. CSV, TSV, ODS, XLS')
    parser.add_argument('-c', '--create', action='store_true', help='Create new files')
    parser.add_argument('--config', nargs=1, help='config for create')
    parser.add_argument('-v', '--verbose', help="Display changes to files")
    parser.add_argument('--update', help="Instead of overwriting files, just update entries")
    parser.add_argument('-o', '--output-dir', type=pathlib.Path, help="Write files to this directory instead of to the repo")
    args = parser.parse_args()

    file = pathlib.Path(args.file)

    paths = None
    muids_mapping = None
    if args.create:
        print('Running in create mode')
        if not args.config:
            # No config file defined
            config_dir = pathlib.Path('./config')
            config_file = (config_dir / file.stem).with_suffix('.json')
            alt_config_file = (config_dir / re.match(r'[a-z]+', file.stem)[0]).with_suffix('.json')
            if not config_file.exists():
                if not alt_config_file.exists():
                    logging.error(f'Expected config file either {config_file} or {alt_config_file}\nA config file can also be passed as a parameter to --config')
                    exit(1)
                config_file = alt_config_file
            print(f'Using config file {config_file}')
        else:
            config_file = pathlib.Path(args.config)
            if not config_file.exists():
                logging.error('Config file does not exist')
                exit(1)
        
        paths, muids_mapping = load_paths_file(config_file)
        
    if args.verbose:
        print(f'paths: {paths}')
        print('muid mapping: {muids_mapping}')

    rows = load_sheet(file)
    
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

            uid_stem = re.match(r'[a-z]+(\d+\.)?', uid)[0]

            rex = re.compile(f'{re.escape(uid_stem)}.*_{muids}')

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
                    print(f'ERROR: Could not find field "{field}" in {config_file}')
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
                if args.verbose and old_value != value:
                    print('{uid}_{field}:{segment_id}: {old_value} -> {value}'.format(**locals()))
                merged_data[segment_id] = value
            
            if args.output_dir:
                out_file = args.output_dir / file.relative_to(repo_dir)            
            else:
                out_file = file

            
            if not out_file.parent.exists():
                out_file.parent.mkdir(parents=True)
            with out_file.open('w') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)
    if errors > 0:
        print(f'{errors} occured while importing sheet, not all data was imported', file=sys.stderr)
        exit(1)
    exit(0)
