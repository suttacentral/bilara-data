import regex
import pathlib

repo_dir = pathlib.Path(__file__).parent.parent

def iter_json_files():
    yield from sorted(repo_dir.glob('[!_.]*/**/[!_]*.json'), key=lambda f: humansortkey(str(f)))

def numericsortkey(string, _split=regex.compile(r'(\d+)').split):
    # if regex.fullmatch('\d+', s) then int(s) is valid, and vice-verca.
    return [int(s) if i % 2 else s for i, s in enumerate(_split(str(string)))]


def humansortkey(string, _split=regex.compile(r'(\d+(?:[.-]\d+)*)').split):
    """
    >>> humansortkey('1.1') > humansortkey('1.0')
    True

    >>> humansortkey('1.0a') > humansortkey('1.0')
    True

    >>> humansortkey('1.0^a') > humansortkey('1.0')
    True
    """
    # With split, every second element will be the one in the capturing group.
    return [numericsortkey(s) if i % 2 else s
            for i, s in enumerate(_split(str(string)))]

def bilarasortkey(string):
    """
    >>> bilarasortkey('1.1') > bilarasortkey('1.0')
    True

    >>> bilarasortkey('1.0a') > bilarasortkey('1.0')
    True

    >>> bilarasortkey('1.0^a') < bilarasortkey('1.0')
    True
    """

    if string[-1].isalpha():
        string = f'{string[:-1]}.{ord(string[-1])}'
    subresult = humansortkey(string)

    result = []
    for i, obj in enumerate(subresult):
        if obj == '':
            obj = 0
        if isinstance(obj, str) and obj and obj[0] == '^':
                result.extend([-1, obj[1:]])
        else:
            result.append(obj)
    
    if isinstance(result[-1], list):
        result.append(0)
    return result


def print_name_if_needed(file, _seen=set()):
    if file not in _seen:
        print(file)
    _seen.add(file)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
