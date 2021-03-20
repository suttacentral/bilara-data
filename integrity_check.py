#!/usr/bin/env python
from typing import Dict, List
import argparse
from pathlib import Path

from sc_renumber_segments.src.sutta_processor.run_app import run

parser = argparse.ArgumentParser()
parser.add_argument('files', type=Path, nargs='*')
args = parser.parse_args()

def _sort_files(file_paths: List[Path]) -> Dict[str, List[Path]]:
    sorted_files: Dict[str: List[Path]] = {}
    comment_files = []
    html_files = []
    ref_files = []
    root_files = []
    trans_files = []
    var_files = []
    for file in file_paths:
        if file.parts[0] == 'comment':
            comment_files.append(file)
        elif file.parts[0] == 'html':
            html_files.append(file)
        elif file.parts[0] == 'reference':
            ref_files.append(file)
        elif file.parts[0] == 'root':
            root_files.append(file)
        elif file.parts[0] == 'translation':
            trans_files.append(file)
        else:
            var_files.append(file)

    sorted_files['comment'] = comment_files
    sorted_files['html'] = html_files
    sorted_files['reference'] = ref_files
    sorted_files['root'] = root_files
    sorted_files['translation'] = trans_files
    sorted_files['variant'] = var_files

    return sorted_files


def test(file_paths: List[Path]) -> int:
    print("The pre-commit hook worked!")
    print(file_paths)
    all_files = _sort_files(file_paths=file_paths)
    # run(cfg_path=Path('sc_renumber_segments/example_config.yaml'))
    return 1


test(file_paths=args.files)
