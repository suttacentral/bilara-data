import re
from hashlib import md5

def transform(string, extra_rules=True):
    """

    * -> <em>
    _ -> <i lang="pi" translate="no">
    ** -> <b>
    [label](ref) -> <a href="/ref">label</a>
    [label](https://example.com) -> <a href="https://example.com">label</a>
    [ref]() or [](ref) -> <a href="/ref">ref</a>
    

    Extra Rules:

    "a -> “a
    a" -> a”
    
    """

    html_mapping = {}

    def subfn(m):
        result = 'TAG' + md5(m[0].encode()).hexdigest()[:20]
        html_mapping[result] = m[0]
        return result
    
    
    string = re.sub(r'<[a-z].*?>', subfn, string)

    if extra_rules:
        string, n = re.subn(r'\"(\w)', r'“\1', string)
        if n > 0:
            print(f'corrected: {string}')

        string, n = re.subn(r'(\w)"', r'\1”', string)
        if n > 0:
            print(f'corrected: {string}')


    # Rules
    string = re.sub(r'\_\_(.*?)\_\_', r'<b>\1</b>', string)
    string = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', string)

    string = re.sub(r'\*(.*?)\*', r'<em>\1</em>', string)
    string = re.sub(r'\_(.*?)\_', r'<i lang="pi" translate="no">\1</i>', string)
    
    def link_fn(m):
        label = m[1]
        link = m[2]

        if label and not link:
            link = label

        if link and not label:
            label = link

        if re.match(r'https?://|#', link) or '/' in link:
            pass
        else:
            link = '/' + link
        
        return f'<a href="{link}">{label}</a>'
    
    string = re.sub(r'\[(.*?)\]\((.*?)\)', link_fn, string)

            
    
    def reverse_subfn(m):
        return html_mapping[m[0]]

    string = re.sub(r'TAG\w{20}', reverse_subfn, string)
    return string.lstrip()
    
parse = transform
