from lxml import etree
import xlwt
import datetime
import time
import pymysql

class Statistics:
    dbConnection = None
    dbCursor = None
    accountList = []
    statistics = {
        'last20':[],
        '2018.7':[],
        '2018.8':[],
        '2018.9':[],
        '2018.10':[],
        '2018.11':[],
        '2018.12':[],
    }
    
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
        self.accountList = self.dbCursor.fetchall()

    def run(self):
        for account in self.accountList:
            feedList = self.getFeedByAccountId(account['id'])
            for key in self.statistics:
                if 'last20'==key:
                    outFeedList = feedList[:20]
                else:
                    arr1 = key.split('.')
                    year = int(arr1[0])
                    month = int(arr1[1])
                    nextMonth = '%s.%s' % (year,month+1) if month < 12 else '%s.1' % (year+1)
                    startTime = datetime.datetime.strptime(key, '%Y.%m')
                    endTime = datetime.datetime.strptime(nextMonth , '%Y.%m')
                    outFeedList = []
                    for feed in feedList:
                        #print(startTime,endTime,feed['pubtime'])
                        if feed['pubtime'] >= startTime and feed['pubtime'] < endTime:
                            outFeedList.append(feed)
                self.statistics[key].append({
                    'name':account['name'],
                    'url':'https://m.weibo.cn/u/%s' % account['uid'],
                    'statictics':dict(**account, **self.getStatistics(outFeedList)),
                    #'weibo_list':feedList
                })
        self.outExcelFile()
        print('done!')

    def getFeedByAccountId(self, accountId):
        self.dbCursor.execute("select * from weibo_feed where account_id = %d order by pubtime desc,id asc;" % accountId)
        feedList = self.dbCursor.fetchall()
        
        return feedList 

    def getStatistics(self, data):
        forwardTotal = sum([i['forward'] for i in data])
        forwardAvg = float(forwardTotal)/float(len(data)) if data else 0
        forwardMax = max([i['forward'] for i in data]) if data else 0
        forwardMin = min([i['forward'] for i in data]) if data else 0

        commentTotal = sum([i['comment'] for i in data])
        commentAvg = float(commentTotal)/float(len(data)) if data else 0
        commentMax = max([i['comment'] for i in data]) if data else 0
        commentMin = min([i['comment'] for i in data]) if data else 0
        
        likeTotal = sum([i['like'] for i in data])
        likeAvg = float(likeTotal)/float(len(data)) if data else 0
        likeMax = max([i['like'] for i in data]) if data else 0
        likeMin = min([i['like'] for i in data]) if data else 0

        result = {
            'forward_total':forwardTotal,
            'forward_avg':forwardAvg,
            'forward_max':forwardMax,
            'forward_min':forwardMin,
            'comment_total':commentTotal,
            'comment_avg':commentAvg,
            'comment_max':commentMax,
            'comment_min':commentMin,
            'like_total':likeTotal,
            'like_avg':likeAvg,
            'like_max':likeMax,
            'like_min':likeMin,
        }
        return result

    def outExcelFile(self):
        book = xlwt.Workbook()
        for key in self.statistics:
            sheet = book.add_sheet(key)
            sheet.write(0, 0, '名称')
            sheet.write(0, 1, '主页')
            sheet.write(0, 2, '粉丝数')
            sheet.write(0, 3, '微博数')
            sheet.write(0, 4, '总转发数')
            sheet.write(0, 5, '平均转发数')
            sheet.write(0, 6, '最大转发数')
            sheet.write(0, 7, '总评论数')
            sheet.write(0, 8, '平均评论数')
            sheet.write(0, 9, '最大评论数')
            sheet.write(0, 10, '总点赞数')
            sheet.write(0, 11, '平均点赞数')
            sheet.write(0, 12, '最大点赞数')
            index = 1
            for row in self.statistics[key]:
                sheet.write(index, 0, row['name'])
                sheet.write(index, 1, row['url'])
                sheet.write(index, 2, row['statictics']['fans'])
                sheet.write(index, 3, row['statictics']['feed'])
                sheet.write(index, 4, row['statictics']['forward_total'])
                sheet.write(index, 5, row['statictics']['forward_avg'])
                sheet.write(index, 6, row['statictics']['forward_max'])
                sheet.write(index, 7, row['statictics']['comment_total'])
                sheet.write(index, 8, row['statictics']['comment_avg'])
                sheet.write(index, 9, row['statictics']['comment_max'])
                sheet.write(index, 10, row['statictics']['like_total'])
                sheet.write(index, 11, row['statictics']['like_avg'])
                sheet.write(index, 12, row['statictics']['like_max'])
                index += 1

            '''
            #创建每个竞品的微博详细数据
            sheet2 = book.add_sheet('sheet2')
            headers2 = ['名称','主页','转发数','评论数','点赞数','发布时间','内容']
            for index2 in range(len(headers2)):
                sheet2.write(0, index2, headers2[index2])
            index = 1
            for row in self.statistics[key]:
                for weibo in row['weibo_list']:
                    columns = ['name','url','forward','comment','like','pubtime','content']
                    for index2 in range(len(columns)):
                        if columns[index2] in ['name','url']:
                            sheet2.write(index, index2, row[columns[index2]])
                        else:
                            sheet2.write(index, index2, weibo[columns[index2]])
                    index += 1
            '''
            book.save('weibo.xls')

statistics = Statistics()
statistics.run()
