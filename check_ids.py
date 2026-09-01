import urllib.request, re
try:
    html = open('dashboard/index.html', encoding='utf-8').read()
    js = open('dashboard/app.js', encoding='utf-8').read()
    ids = re.findall(r"getElementById\('([^']+)'\)", js)
    missing = [i for i in set(ids) if 'id="' + i + '"' not in html and "id='" + i + "'" not in html]
    print('Missing IDs:', missing)
except Exception as e:
    print('Error:', e)
