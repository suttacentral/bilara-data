import regex
from Bio import pairwise2
from Levenshtein import jaro_winkler
from difflib import SequenceMatcher

GAP_CHAR = None

def normalize(s):
    s = s.replace('ṁ', 'ṃ')
    s = s.replace('ṅ', 'ṃ')
    s = s.strip()
    s = s.casefold()
    s = regex.sub(r'[^\p{alpha}\s]', '', s)
    s = regex.sub(r'\s+', r'', s)
    return s

def score_match(t_a, t_b):
    string_a = normalize(t_a[0])
    string_b = normalize(t_b[0])
    if string_a == string_b:
        return 2

    sm = SequenceMatcher(a=string_a, b=string_b)

    return 1.2 * sm.ratio() - 0.2

def pairwise_align(a, b):
    normalized_a = [normalize(t[0]) for t in a]
    normalized_b = [normalize(t[0]) for t in b]

    return pairwise2.align.globalcx(a, b, match_fn=score_match, gap_char=[GAP_CHAR])

def align(a, b):
    seq = pairwise_align(a, b)[0]
    return list(zip(seq.seqA, seq.seqB))

def root_alignment_mapping(current_root_strings, stale_root_strings):
    mapping = {}
    aligned = align(current_root_strings, stale_root_strings)

    for current, stale in aligned:
        if current == None or stale == None:
            continue
        mapping[stale[1]] = current[1]
    return mapping
