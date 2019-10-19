import json,requests,re,unidecode
from bs4 import BeautifulSoup


url = 'http://naturalstattrick.com/playerteams.php?fromseason=20192020&thruseason=20192020&stype=2&sit=5v5&score=all&stdoi=oi&rate=n&team=BUF&pos=S&loc=B&toi=0&gpfilt=none&fd=&td=&tgp=410&lines=single&draftteam=ALL'
requester = requests.get(url)
content = requester.content
content_soup = BeautifulSoup(content, "lxml")
para = content_soup.find_all("tr")
for table_row in para:
    table_row = str(table_row)
    a = re.findall(r'>([^<]*)<', table_row)
    print(a)
    print(type(a))
    exit(1)