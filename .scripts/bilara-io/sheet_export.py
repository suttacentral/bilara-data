#!/usr/bin/env python3

import re
import csv
import pathlib
import argparse
from get_data import get_data

repo_dir = pathlib.Path(__file__).resolve().parent.parent.parent

def save_sheet(rows, filename):
    
    m = re.search(r'.*(\.\w+)$', filename)
    if not m:
        suffix = '.csv'
    else:
        suffix = m[1]  
    
    if suffix in {'.csv', '.tsv'}:
        import csv

        dialect = {
            '.csv': csv.excel,
            '.tsv': csv.excel_tab
        }[suffix]

        with open(filename, 'w', encoding='utf8', newline='') as f:
            writer = csv.writer(f, dialect=dialect)
            writer.writerows(rows)
    else:
        import pyexcel
        pyexcel.isave_as(array=rows, dest_file_name=args.out or (','.join(args.uid) + '.ods'))
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Export Spreadsheet")
    parser.add_argument('uid', nargs='+', help='One or more sutta UID to export')
    parser.add_argument('out', help='Output file')
    parser.add_argument('--include', default='', help='Filter by MUID. Comma seperated, + for and\nexample: "root,translation+en"')
    parser.add_argument('--exclude', default='', help='Filter by MUID. Comma seperated')
    args = parser.parse_args()

    uids = frozenset(args.uid)
    if args.include:
        include_filter = {frozenset(filter.split('+')) if '+' in filter else filter for filter in args.include.split(',')}
    else:
        include_filter = None
    if args.exclude:
        exclude_filter = frozenset(args.exclude.split(','))
    else:
        exclude_filter = None
    
    rows = get_data(repo_dir, uids, include_filter, exclude_filter)

    save_sheet(rows, args.out)



