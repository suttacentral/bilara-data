import re
import json
import pathlib

from common import iter_json_files, bilarasortkey, json_load
from typing import Generator, Optional

def muid_sort_key(string):
    if string.startswith('root'):
        return (0, string)
    elif string.startswith('translation'):
        return (1, string)
    elif string.startswith('markup'):
        return (2, string)
    else:
        return (3, string)

def yield_rows(muid_strings, file_uid_mapping):
    fields = ['segment_id'] + muid_strings
    yield fields

    field_mapping = {field:i for i, field in enumerate(fields)}
    
    for file_num, (uid, file_mapping) in enumerate(sorted(file_uid_mapping.items(), key=bilarasortkey)):
        data = {}
        segment_ids = set()
        for muid_string in muid_strings:
            if muid_string in file_mapping:
                file = file_mapping[muid_string]
                
                try:
                    file_data = json_load(file)
                except json.decoder.JSONDecodeError:
                    exit(1)
                
                i = field_mapping[muid_string]
                for segment_id, value in file_data.items():
                    if segment_id not in data:
                        data[segment_id] = [segment_id] + [''] * (len(fields) - 1)
                    data[segment_id][i] = value
        
        for segment_id in sorted(data.keys(), key=bilarasortkey):
            yield data[segment_id]
        
        if file_num < len(file_uid_mapping) - 1:
            yield [''] * len(fields)

def get_data(repo_dir: pathlib.Path, uids: set[str], include_filter: Optional[set[set[str]]] = None, exclude_filter: Optional[set[str]] = None) -> Generator[list[str], None, None]:
    """
    repo_dir is a path to the bilara-data repository or structurally equivilant data

    uids is a set of the uids to get the data for, this can be a single text uid such as {dn2}, a single folder uid such as {dn}
    or multiple, such as {dn1,dn2,dn3,dn4,dn5,dn6,dn7,dn8,dn9,dn10}

    include_filter is a set of muids or frozensets of muids {frozenset({'translation','en','sujato'}),'root','reference'}, if None everything is included
    
    exclude_filter is a set of muids, anything matching will be excluded, e.g. {'comment'}. If None nothing is excluded.

    Returns a generator that yields rows of data suitable for feeding to csv_writer. The first result is the fields
    which will always start with the segment_id and be followed by root, translation and markup fields (provided they
    are included by filters), remaining included fields are sorted in simple alphabetical order.
    Subsequent results are rows of data.
    When multiple texts are processed each text is seperated by a list of empty strings.
    """

    file_uid_mapping = {}
    for file in iter_json_files(repo_dir):
        
        try:
            uid, muids_string = file.stem.split('_')
        except:
            print(file)
            raise

        if not (uid in uids or any(part in uids for part in file.parent.parts)):
            continue
            
        print('Reading {}'.format(str(file.relative_to(repo_dir))))

        muids = frozenset(muids_string.split('-'))
        if include_filter:
            for muid in include_filter:
                if isinstance(muid, frozenset):
                    if muids.intersection(muid) == muid:
                        break
                else:
                    if muid in muids:
                        break
            else:
                continue
        
        if exclude_filter and exclude_filter.intersection(muids):
            continue
        
        if uid not in file_uid_mapping:
            file_uid_mapping[uid] = {}
        file_uid_mapping[uid][muids_string] = file
    
    if not file_uid_mapping:
        print('No matches for {}'.format(",".join(args.uid)), file=sys.stderr)
        exit(1)
        
    muid_strings = set()
    for keys in file_uid_mapping.values():
        muid_strings.update(keys)
    
    muid_strings = sorted(muid_strings, key=muid_sort_key)
    
    return yield_rows(muid_strings, file_uid_mapping)
