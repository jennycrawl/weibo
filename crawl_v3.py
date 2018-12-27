import os
import sys
import time
import datetime
import json
import pymysql
import requests
import math
import random
import asyncio 
from aiohttp import ClientSession

class CrawlWeibo:
    accountAction = 'all'
    debugAction = ''
    proxyFileName = 'proxy.txt'
    feedListFileName = 'feed_list.txt'
    accountInfoFileName = 'account_info.txt'
    accountList = []
    proxyList = []
    def __init__(self):
        if len(sys.argv) > 1 and sys.argv[1] and sys.argv[1] != 'all':
            self.accountAction = sys.argv[1]
        if 'debug' in sys.argv:
            self.debugAction = True
        dbConnection = pymysql.connect(
            host='47.98.110.129',
            user='root',
            password='123456',
            database='jenny_crawl',
            charset='utf8',
            cursorclass = pymysql.cursors.DictCursor
        )
        cursor = dbConnection.cursor()
        cursor.execute("select * from weibo_account;")
        self.accountList = cursor.fetchall()
        dbConnection.close()

        self.loadProxy()

    def loadProxy(self):
        for line in open(self.proxyFileName):
            arr = line.strip().split('\t')
            self.proxyList.append({
                'http':'http://%s:%s' % (arr[0],arr[1]),
                'https':'http://%s:%s' % (arr[0],arr[1])
            })

    def run(self):
        accountInfoFile = open(self.accountInfoFileName, 'w')
        feedListFile = open(self.feedListFileName, 'w')
        urlList = []
        for account in self.accountList:
            name = account['name']
            uid = account['uid']
            if self.accountAction != 'all' and self.accountAction != name:
                continue

            url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=%s' % uid
            try:
                data = json.loads(requests.get(url, timeout=5).text)
                #data = json.loads(requests.get(url).text)
            except requests.RequestException as e:
                print(e)
                continue
            accountInfoFile.write(json.dumps(data,ensure_ascii = False) + '\n')
            tabs = data.get('data',{}).get('tabsInfo',{}).get('tabs',[])
            containerId = tabs[1].get('containerid',0) if tabs else None
            feedCount = data.get('data',{}).get('userInfo',{}).get('statuses_count',0)
            pageCount = math.ceil(float(feedCount)/10.0)
            if not containerId or not feedCount:
                continue
            urlList.append({
                'uid':uid,
                'url':'https://m.weibo.cn/api/container/getIndex?type=uid&value=%s&containerid=%s' % (uid,containerId)
            })
            for url in ['https://m.weibo.cn/api/container/getIndex?type=uid&value=%s&containerid=%s&page=%d' % (uid,containerId,i) for i in list(range(2, pageCount + 1))]:
                urlList.append({'uid':uid,'url':url})

            urlList = ['https://m.weibo.cn/api/container/getIndex?type=uid&value=%s&containerid=%s' % (uid,containerId)]
            for url in urlList + ['https://m.weibo.cn/api/container/getIndex?type=uid&value=%s&containerid=%s&page=%d' % (uid,containerId,i) for i in list(range(2, pageCount + 1))]:
                time.sleep(0.5)
                try:
                    #data = json.loads(requests.get(url, proxies = random.choice(self.proxyList),timeout=2).text)
                    data = json.loads(requests.get(url, timeout=5).text)
                    feedListFile.write(uid + '\t' + json.dumps(data, ensure_ascii = False) + '\n')
                except requests.RequestException as e:
                    print(e)
                    continue

    def crawlOnePage(self, url, isGetOtherPage = False):
        if self.debugAction:
            print(url)
        pageContent = ''
        try:
            self.chromeDriver.get(url)
            self.chromeDriver.delete_all_cookies()
            for cookie in self.cookieList:
                self.chromeDriver.add_cookie(cookie)
            self.chromeDriver.get(url)
            try:
                element = WebDriverWait(self.chromeDriver, 1).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@action-type="feed_list_item"]'))
                )
            except:
                pass
            height = self.chromeDriver.find_element_by_tag_name('body').size.get('height', 0)
            if self.debugAction:
                print(height)
            #模拟浏览器下拉
            while 1:
                self.chromeDriver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
                try:
                    element = WebDriverWait(self.chromeDriver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@action-type="feed_list_page_morelist"]'))
                    )
                except:
                    pass
                newHeight = self.chromeDriver.find_element_by_tag_name('body').size.get('height', 0)
                if self.debugAction:
                    print(newHeight)
                if newHeight == height:
                    break
                height = newHeight
            pageContent = self.chromeDriver.page_source
        except WebDriverException as msg:
            if self.debugAction:
                print(msg)
        if isGetOtherPage:
            try:
                otherPageNodes = self.chromeDriver.find_elements_by_xpath(\
                    '//div[@action-type="feed_list_page_morelist"]/ul/li[not(contains(@class,"cur"))]/a')
                otherPageList = [i.get_attribute('href') for i in otherPageNodes]
            except WebDriverException as msg:
                if self.debugAction:
                    print(msg)
                otherPageList = []
            return pageContent,otherPageList[::-1]
        else:
            return pageContent

crawlWeibo = CrawlWeibo()
crawlWeibo.run()

#driver = webdriver.PhantomJS()    
#driver.get('http://www.baidu.com/')
#print(driver.page_source)
