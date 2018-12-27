from lxml import etree
import xlwt
import datetime
import time
import json
import pymysql

class ParseWeibo:
    dbConnection = None
    dbCursor = None
    inputFileName = 'page_content.txt'
    pageContent = []
    statistics = []
    
    def __init__(self):
        self.dbConnection = pymysql.connect(
            host='47.98.110.129',
            user='root',
            password='123456',
            database='jenny_crawl',
            charset='utf8',
            cursorclass = pymysql.cursors.DictCursor
        )
        self.dbCursor = self.dbConnection.cursor()

    def run(self):
        for line in open(self.inputFileName):
            row = json.loads(line)
            if not row:
                continue
            #self.pageContent.append({'name':arr2[0],'url':arr2[1],'content_list':arr2[2].split('`3')})
            self.parsePageContent(row['name'], row['content_list'])
        print('done!')

    def parsePageContent(self, name, contentList):
        [accountInfo,feedList] = self.parseOneAccountContent(contentList)
        self.updateAccountInfo(name, accountInfo)
        self.updateFeedList(name, feedList)

    def parseOneAccountContent(self, contentList):
        accountInfo = self.parseAccountInfo(contentList[0])
        feedList = self.parseFeedList(contentList)

        return accountInfo,feedList

    def parseAccountInfo(self, content):
        accountInfo = {}
        page = etree.HTML(content)
        #粉丝数
        counterNode = page.xpath('//table[@class="tb_counter"]')
        #print(counterNode)
        if not counterNode:
            accountInfo = {
                'attention' :0,
                'fans'      :0,
                'feed'     :0    
            }
        else:
            attentionNode = counterNode[0].xpath('./tbody/tr/td[1]//strong')
            fansNode = counterNode[0].xpath('./tbody/tr/td[2]//strong')
            weiboNode = counterNode[0].xpath('./tbody/tr/td[3]//strong')
            accountInfo = {
                'attention' :int(attentionNode[0].text) if attentionNode and attentionNode[0].text.isdigit() else 0,
                'fans'      :int(fansNode[0].text) if fansNode and fansNode[0].text.isdigit() else 0,
                'feed'     :int(weiboNode[0].text) if weiboNode and weiboNode[0].text.isdigit() else 0,
            }
        return accountInfo

    def updateAccountInfo(self, accountName, accountInfo):
        sql = '''
SELECT
    weibo_account.id,
    weibo_account.name,
    weibo_account_info.*
FROM
    weibo_account_info
RIGHT JOIN weibo_account ON weibo_account_info.account_id = weibo_account.id
WHERE
    weibo_account.name = '%s';
        ''' % (accountName)
        self.dbCursor.execute(sql)
        oldInfo = self.dbCursor.fetchone()
        if not oldInfo:
            return
        currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not oldInfo['account_id']:
            sql = "INSERT INTO weibo_account_info (account_id,attention,fans,feed,update_time) VALUES (%d,%d,%d,%d,'%s');" \
                % (oldInfo['id'], accountInfo['attention'], accountInfo['fans'], accountInfo['feed'], currentTime)
        else:
            sql = "UPDATE weibo_account_info SET attention=%d,fans=%d,feed=%d,update_time='%s' where account_id=%d limit 1;" \
                % (accountInfo['attention'], accountInfo['fans'], accountInfo['feed'], currentTime, oldInfo['account_id'])
        print(sql)
        self.dbCursor.execute(sql)
        self.dbConnection.commit()

    def updateFeedList(self, accountName, feedList):
        sql = "SELECT * FROM weibo_account WHERE name = '%s';" % accountName
        self.dbCursor.execute(sql)
        account = self.dbCursor.fetchone()
        if not account:
            return
        sql = "SELECT * FROM weibo_feed WHERE account_id = %s;" % account['id']
        self.dbCursor.execute(sql)
        oldFeedList = self.dbCursor.fetchall()
        oldFeedListDict = dict(zip([i['mid'] for i in oldFeedList], oldFeedList))
        currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for feed in feedList:
            oldFeed = oldFeedListDict.get(feed['mid'], {})
            if not oldFeed:
                sql = '''
INSERT INTO weibo_feed 
(mid,account_id,forward,comment,`like`,pubtime,create_time,update_time)
VALUES ('%s',%d,%d,%d,%d,'%s','%s','%s');
                ''' % (feed['mid'],account['id'],feed['forward'],feed['comment'],feed['like'],feed['pubtime'], \
                currentTime,currentTime)
            elif feed['forward'] != oldFeed['forward'] or feed['comment'] != oldFeed['comment'] or feed['like'] != oldFeed['like']:
                sql = "UPDATE weibo_feed SET account_id=%d,forward=%d,comment=%d,`like`=%d,pubtime='%s',update_time='%s' where mid='%s' limit 1;" % (account['id'],feed['forward'],feed['comment'],feed['like'],feed['pubtime'],currentTime,feed['mid'])
            else:
                continue
            print(sql)
            #self.dbCursor.execute(sql)
        self.dbConnection.commit()
    
    def parseFeedList(self, contentList):
        feedList = []
        for content in contentList:
            page = etree.HTML(content)
            #每条微博信息
            feedNodeList = page.xpath('//div[@action-type="feed_list_item"]')
            for feedNode in feedNodeList:
                mid = feedNode.get('mid')
                contentNode = feedNode.xpath('.//div[@class="WB_detail"]/div[@node-type="feed_list_content"]')
                pubtimeNode = feedNode.xpath('.//div[@class="WB_detail"]/div[contains(@class,"WB_from")]/a[@node-type="feed_list_item_date"]/@title')
                forwardNode = feedNode.xpath('.//div[@class="WB_handle"]/ul/li[2]//span[contains(@class,"S_line1")]/span/em[2]')
                commentNode = feedNode.xpath('.//div[@class="WB_handle"]/ul/li[3]//span[contains(@class,"S_line1")]/span/em[2]')
                likeNode = feedNode.xpath('.//div[@class="WB_handle"]/ul/li[4]//span[contains(@class,"S_line1")]/span/em[2]')

                feedList.append({
                    'mid':mid,
                    'content':contentNode[0].text.strip() if contentNode else '',
                    'pubtime':pubtimeNode[0],
                    'pubtime_stamp':int(time.mktime(time.strptime(pubtimeNode[0], "%Y-%m-%d %H:%M"))),
                    'forward':int(forwardNode[0].text) if forwardNode and forwardNode[0].text.isdigit() else 0,
                    'comment':int(commentNode[0].text) if commentNode and commentNode[0].text.isdigit() else 0,
                    'like':int(likeNode[0].text) if likeNode and likeNode[0].text.isdigit() else 0,
                })
        return feedList



parseWeibo = ParseWeibo()
parseWeibo.run()
