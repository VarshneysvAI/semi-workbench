import httpx
from bs4 import BeautifulSoup
res = httpx.post('https://html.duckduckgo.com/html/', data={'q':'Appliance Dealers Cooperative PDSH4816AF specification'}, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(res.text, 'html.parser')
for a in soup.select('.result__a'):
    print(a['href'])
