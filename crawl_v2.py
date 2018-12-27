import os
import sys
import time
import datetime
import json
import pymysql

class CrawlWeibo:
    accountAction = 'all'
    debugAction = ''
    chromeDriver = None
    outFileName = 'page_content.txt'
    cookieStr = 'MLOGIN=0; expires=Tue, 25-Dec-2018 07:34:38 GMT; Max-Age=3600; path=/; domain=.weibo.cn
set-cookie: M_WEIBOCN_PARAMS=luicode%3D10000011%26lfid%3D100103type%253D1%2526q%253DFOTA%25E5%25AE%2598%25E6%2596%25B9%25E5%25BE%25AE%25E5%258D%259A%26fid%3D1076036545296757%26uicode%3D10000011; expires=Tue, 25-Dec-2018 06:44:38 GMT; Max-Age=600; path=/; domain=.weibo.cn; HttpOnly'
    cookieDomain = '.weibo.com'
    cookiePath = '/'
    cookieList = []
    accountList = []
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

        #cookie
        for line1 in self.cookieStr.strip().split(';'):
            arr2 = line1.strip().split('=')
            if len(arr2) < 2:
                continue
            name = arr2[0].strip()
            value = arr2[1].strip()
            if not name:
                continue
            self.cookieList.append({
                'name':name,
                'value':value,
                'domain':self.cookieDomain,
                'path':self.cookiePath
            })

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        #crontab运行时需要加上chromedriver绝对路径
        self.chromeDriver = webdriver.Chrome(options=chrome_options)

    def run(self):
        outFile = open(self.outFileName, 'w')
        for account in self.accountList:
            name = account['name']
            url = account['url']
            if self.accountAction != 'all' and self.accountAction != name:
                continue

            pageContentList = []
            [pageContent,otherPageList] = self.crawlOnePage(url, True)
            if not pageContent:
                continue
            for otherPage in otherPageList:
                print(otherPage)
            continue
            outFile.write(json.dumps({'name':name,'url':url,'content':pageContent}, ensure_ascii = False) + '\n')
            while nextPage:
                [pageContent,nextPage] = self.crawlOnePage(nextPage)
                if not pageContent:
                    continue
                outFile.write(json.dumps({'name':name,'url':url,'content':pageContent}, ensure_ascii = False) + '\n')
        self.chromeDriver.quit()
        '''
        driver = webdriver.Chrome()
        driver.get(url)
        driver.delete_all_cookies()
        driver.add_cookie(self.cookie)
        driver.get(url)
        outFile.write('%s`2%s`2%s`1' % (name,url,driver.page_source))
        '''
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
