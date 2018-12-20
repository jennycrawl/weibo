import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

class CrawlWeibo:
    chromeDriver = None
    urlFileName = 'url_list.txt'
    outFileName = 'page_content.txt'
    #cookieStr = 'SINAGLOBAL=1191667905077.3381.1436279964765; ULV=1541488702660:1:1:1:7813753085219.45.1541488702623:; wvr=6; UOR=,,login.sina.com.cn; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWxmd2YbyypZovNB1XTl7Md5JpX5KMhUgL.Fo2RSon7SoBce0M2dJLoIpnLxK-L1h5L1K.LxK.LBonL1-9QMg_u9cjt; YF-Page-G0=d52660735d1ea4ed313e0beb68c05fc5; ALF=1573572899; SSOLoginState=1542036901; SCF=AlDOMz1UW2pT9nUIRY1TWFq7uAGyCxzSohmcI64qwwcJFVmSWtE65xTvX4Yn13iXeiR_vkhBdjPi8zb_ObD_kQc.; SUB=_2A2527e31DeRhGedG7VoR9irKyDuIHXVVm1g9rDV8PUNbmtBeLWL5kW9NUQ3yp5QTPWnA-RlHjn-a_DTnPKkj60jS; SUHB=09PM1m4iqmIxOY'
    cookieStr = 'YF-Page-G0=a1c00fe9e544064d664e61096bd4d187; SUB=_2AkMsve51f8NxqwJRmPwcxGnnbY1xyQDEieKa4R-uJRMxHRl-yT83qhQrtRB6Bz3AmkMGDSDmgKgnDZuKt56PBNWrAgbQ; SUBP=0033WrSXqPxfM72-Ws9jqgMF55529P9D9WWE4qv6GB0aJBu-ksW9uQ1r'
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
        try:
            for account in self.accountList:
                name = account['name']
                url = account['url']
                if 'FOTA官方微博' != name:
                    continue
                self.chromeDriver.get(url)
                self.chromeDriver.delete_all_cookies()
                for cookie in self.cookieList:
                    self.chromeDriver.add_cookie(cookie)
                self.chromeDriver.get(url)
                time.sleep(1)
                outFile.write('%s`2%s`2%s`1' % (name,url,self.chromeDriver.page_source))
                #self.chromeDriver.close()
                #os.system("ps -ef | grep chrome | grep -v grep | awk '{print $2}' | xargs kill -9")
            self.chromeDriver.quit()
        except WebDriverException as msg:
            print(msg)
            self.chromeDriver.quit()
        '''
        driver = webdriver.Chrome()
        driver.get(url)
        driver.delete_all_cookies()
        driver.add_cookie(self.cookie)
        driver.get(url)
        outFile.write('%s`2%s`2%s`1' % (name,url,driver.page_source))
        '''

crawlWeibo = CrawlWeibo()
crawlWeibo.run()

#driver = webdriver.PhantomJS()    
#driver.get('http://www.baidu.com/')
#print(driver.page_source)
