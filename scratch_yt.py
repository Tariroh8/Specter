import urllib.request
import urllib.parse
import re

query = 'rick roll'
url = f'https://www.youtube.com/results?search_query={urllib.parse.quote(query)}'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')
match = re.search(r'"videoId":"([^"]+)"', html)
if match:
    print(f'Found: https://www.youtube.com/watch?v={match.group(1)}')
else:
    print('Not found')
