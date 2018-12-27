import os
import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

class CrawlWeibo:
    chromeDriver = None
    urlFileName = 'url_list2.txt'
    outFileName = 'page_content.txt'
    cookieStr = 'SINAGLOBAL=5534878588822.174.1515075293726; UOR=passport.weibo.com,weibo.com,www.baidu.com; un=18667919082; wb_view_log_1868064637=1366*7681; Ugrow-G0=5b31332af1361e117ff29bb32e4d8439; ALF=1576896093; SSOLoginState=1545360094; SCF=An8BaW5wgbriHRbETfFQdIHn7oWK2RwRGWDdjMHFBe2w4Kan1yQO_a2PLdra1eis6OG9fOxkTMgUZaRCv_WgG0M.; SUB=_2A25xGCKPDeRhGedG7VoR9irKyDuIHXVSbBNHrDV8PUNbmtBeLVijkW9NUQ3yp1aR5vqutlycdhD1tLmyHkfI6lk5; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWxmd2YbyypZovNB1XTl7Md5JpX5KzhUgL.Fo2RSon7SoBce0M2dJLoIpnLxK-L1h5L1K.LxK.LBonL1-9QMg_u9cjt; SUHB=0YhgSmpJQry9WX; wvr=6; YF-V5-G0=b4445e3d303e043620cf1d40fc14e97a; YF-Page-G0=046bedba5b296357210631460a5bf1d2; _s_tentry=login.sina.com.cn; Apache=8358999518517.582.1545360098139; ULV=1545360098180:11:4:2:8358999518517.582.1545360098139:1545295101568'
    #cookieStr = 'YF-Page-G0=a1c00fe9e544064d664e61096bd4d187; SUB=_2AkMsve51f8NxqwJRmPwcxGnnbY1xyQDEieKa4R-uJRMxHRl-yT83qhQrtRB6Bz3AmkMGDSDmgKgnDZuKt56PBNWrAgbQ; SUBP=0033WrSXqPxfM72-Ws9jqgMF55529P9D9WWE4qv6GB0aJBu-ksW9uQ1r'
    cookieDomain = '.weibo.com'
    cookiePath = '/'
    cookieList = []
    accountList = []
    def __init__(self):
        for line in open(self.urlFileName):
            arr1 = line.strip().split('\t')
            if len(arr1) < 2:
                continue
            self.accountList.append({'name':arr1[0],'url':arr1[1]})

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
            #if 'ZB中币' != name:
            #    continue

            pageContentList = []
            [pageContent,nextPage,earliestPubtime] = self.crawlOnePage(url)
            if not pageContent:
                continue
            pageContentList.append(pageContent)
            startTime = datetime.datetime.strptime('2018-07-01 00:00', "%Y-%m-%d %H:%M")
            '''
            while nextPage:
                [pageContent,nextPage,earliestPubtime] = self.crawlOnePage(nextPage)
                if not pageContent:
                    continue
                pageContentList.append(pageContent)
                if earliestPubtime and earliestPubtime < startTime:
                    break
            '''
            outFile.write('%s`2%s`2%s`1' % (name,url,'`3'.join(pageContentList))) 
        self.chromeDriver.quit()
        '''
        driver = webdriver.Chrome()
        driver.get(url)
        driver.delete_all_cookies()
        driver.add_cookie(self.cookie)
        driver.get(url)
        outFile.write('%s`2%s`2%s`1' % (name,url,driver.page_source))
        '''
    def crawlOnePage(self, url):
        print(url)
        pageContent = ''
        try:
            self.chromeDriver.get(url)
            self.chromeDriver.delete_all_cookies()
            for cookie in self.cookieList:
                self.chromeDriver.add_cookie(cookie)
            self.chromeDriver.get(url)
            time.sleep(1)
            height = self.chromeDriver.find_element_by_tag_name('body').size.get('height', 0)
            print(height)
            #模拟浏览器下拉
            while 1:
                self.chromeDriver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
                time.sleep(2)
                newHeight = self.chromeDriver.find_element_by_tag_name('body').size.get('height', 0)
                print(newHeight)
                if newHeight == height:
                    break
                height = newHeight
            pageContent = self.chromeDriver.page_source
            #outFile.write('%s`2%s`2%s`1' % (name,url,self.chromeDriver.page_source))
            #self.chromeDriver.close()
            #os.system("ps -ef | grep chrome | grep -v grep | awk '{print $2}' | xargs kill -9")
            #self.chromeDriver.quit()
        except WebDriverException as msg:
            print(msg)
            #self.chromeDriver.quit()
        try:
            nextPage = self.chromeDriver.find_element_by_xpath('//div[@class="W_pages"]/a[contains(@class,"page next")]').get_attribute('href')
            pubtime = self.chromeDriver.find_element_by_xpath('//div[@class="WB_detail"]/div[contains(@class,"WB_from")]/a[@node-type="feed_list_item_date"]').get_attribute('title')
            earliestPubtime = self.chromeDriver.find_elements_by_xpath('//div[@class="WB_detail"]/div[contains(@class,"WB_from")]/a[@node-type="feed_list_item_date"]')[-1].get_attribute('title')
            earliestPubtime = datetime.datetime.strptime(earliestPubtime, "%Y-%m-%d %H:%M")
            print(pubtime,earliestPubtime)
        except WebDriverException as msg:
            print(msg)
            nextPage = ''
            earliestPubtime = None
        return pageContent,nextPage,earliestPubtime

crawlWeibo = CrawlWeibo()
crawlWeibo.run()

#driver = webdriver.PhantomJS()    
#driver.get('http://www.baidu.com/')
#print(driver.page_source)
