from lxml import etree
import xlwt
import datetime
import time
import json
import pymysql

class ParseWeibo:
    dbConnection = None
    dbCursor = None
    accountInfoFileName = 'account_info.txt'
    feedListFileName = 'feed_list.txt'
    pageContent = []
    statistics = []
    accountMap = {}
    
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
        self.dbCursor.execute("select * from weibo_account;")
        accountList = self.dbCursor.fetchall()
        self.accountMap = dict(zip([i['uid'] for i in accountList], accountList))

        '''
        print('刚刚',self.formatTime('刚刚'))
        print('10秒前',self.formatTime('10秒前'))
        print('5分钟前',self.formatTime('5分钟前'))
        print('2小时前',self.formatTime('2小时前'))
        print('昨天',self.formatTime('昨天'))
        print('今天',self.formatTime('今天'))
        print('12-22',self.formatTime('12-22'))
        print('2017-12-22',self.formatTime('2017-12-22'))
        '''

    def run(self):
        for line in open(self.accountInfoFileName):
            row = json.loads(line)
            if not row:
                continue
            accountInfo = self.parseAccountInfo(row)
            if accountInfo and accountInfo.get('uid'):
                self.updateAccountInfo(accountInfo)

        for line in open(self.feedListFileName):
            arr = line.strip().split('\t')
            if len(arr) < 2:
                continue
            uid = arr[0]
            row = json.loads(arr[1])
            if not row:
                continue
            feedList = self.parseFeedList(row)
            if feedList:
                self.updateFeedList(uid, feedList)
        print('done!')

    def parseAccountInfo(self, data):
        result = {}
        userInfo = data.get('data',{}).get('userInfo',{})
        if not userInfo:
            return result
        result = {
            'uid':userInfo.get('id',0),
            'attention':userInfo.get('follow_count',0),
            'fans':userInfo.get('followers_count',0),
            'feed':userInfo.get('statuses_count',0),
        }
        return result

    def parseFeedList(self, data):
        result = []
        for card in data.get('data',{}).get('cards',[]):
            mblog = card.get('mblog',{})
            if not mblog or not mblog.get('mid'):
                continue
            row = {
                'mid':mblog.get('mid',''),
                'forward':mblog.get('reposts_count',0),
                'comment':mblog.get('comments_count',0),
                'like':mblog.get('attitudes_count',''),
                'pubtime':self.formatTime(mblog.get('created_at',''))
            }
            result.append(row)
            #print(mblog.get('created_at',''),row['pubtime'])
        return result

    def updateAccountInfo(self, accountInfo):
        uid = accountInfo['uid']
        if str(uid) not in self.accountMap:
            return
        currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = "UPDATE weibo_account SET attention=%d,fans=%d,feed=%d,update_time='%s' where uid=%d limit 1;" \
                % (accountInfo['attention'], accountInfo['fans'], accountInfo['feed'], currentTime, uid)
        self.dbCursor.execute(sql)
        self.dbConnection.commit()
    
    def updateFeedList(self, uid, feedList):
        accountId = self.accountMap.get(uid,{}).get('id')
        if not accountId:
            return
        sql = "SELECT * FROM weibo_feed WHERE account_id = %s;" % accountId
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
                ''' % (feed['mid'],accountId,feed['forward'],feed['comment'],feed['like'],feed['pubtime'], \
                currentTime,currentTime)
            elif feed['forward'] != oldFeed['forward'] or feed['comment'] != oldFeed['comment'] or feed['like'] != oldFeed['like']:
                sql = "UPDATE weibo_feed SET account_id=%d,forward=%d,comment=%d,`like`=%d,pubtime='%s',update_time='%s' where mid='%s' limit 1;" % (accountId,feed['forward'],feed['comment'],feed['like'],feed['pubtime'],currentTime,feed['mid'])
            else:
                continue
            #print(sql)
            self.dbCursor.execute(sql)
        self.dbConnection.commit()
         

    def formatTime(self, publish_time):
        currentYear = datetime.datetime.now().strftime('%Y')
        result = ''
        if "刚刚" in publish_time:
            result = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:00')
        elif "秒" in publish_time:
            second = publish_time[:publish_time.find("秒")]
            second = datetime.timedelta(seconds=int(second))
            result = (
                datetime.datetime.now() - second).strftime(
                "%Y-%m-%d %H:%M:%S")
        elif "分钟" in publish_time:
            minute = publish_time[:publish_time.find("分钟")]
            minute = datetime.timedelta(minutes=int(minute))
            result = (
                datetime.datetime.now() - minute).strftime(
                "%Y-%m-%d %H:%M:00")
        elif "小时" in publish_time:
            hour = publish_time[:publish_time.find("小时")]
            hour = datetime.timedelta(hours=int(hour))
            result = (
                datetime.datetime.now() - hour).strftime(
                "%Y-%m-%d %H:00:00")
        elif "今天" in publish_time:
            result = datetime.datetime.now().strftime("%Y-%m-%d 00:00:00")
        elif "昨天" in publish_time:
            result = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
        elif len(publish_time) > 5:
            result = datetime.datetime.strptime(publish_time, '%Y-%m-%d').strftime("%Y-%m-%d 00:00:00")
        else:
            result = datetime.datetime.strptime(publish_time, '%m-%d').strftime(currentYear + "-%m-%d 00:00:00")
        return result

parseWeibo = ParseWeibo()
parseWeibo.run()
