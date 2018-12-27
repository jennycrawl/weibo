import os
import sys
import time
import datetime
import json
import pymysql
import requests
from lxml import etree

outFile = open('proxy.txt', 'w')
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
}
content = requests.get('https://www.xicidaili.com/nn/', headers=headers).text
page = etree.HTML(content)
trNodes = page.xpath('//table[@id="ip_list"]/tr')
for trNode in trNodes:
    ipNodes = trNode.xpath('./td[2]')
    portNodes = trNode.xpath('./td[3]')
    existNode = trNode.xpath('./td[9]')
    if not ipNodes or not portNodes:
        continue
    ip = ipNodes[0].text
    port = portNodes[0].text
    exist = existNode[0].text
    if '分钟' in exist:
        continue
    outFile.write('%s\t%s\n' % (ip, port))
    
