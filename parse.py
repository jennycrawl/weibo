from lxml import etree
import xlwt
import datetime

class ParseWeibo:
    inputFileName = 'page_content.txt'
    pageContent = []
    statistics = []
    
    def __init__(self):
        arr1 = open(self.inputFileName).read().strip().split('`1')
        for line2 in arr1:
            arr2 = line2.split('`2')
            if len(arr2) < 3:
                continue
            #if 'BitMEX' == arr2[0]:
            #    print(arr2[2])
            #else:
            #    continue
            self.pageContent.append({'name':arr2[0],'url':arr2[1],'content':arr2[2]})

    def run(self):
        self.parsePageContent()
        self.outExcelFile()
        print('done!')

    def parsePageContent(self):
        for row in self.pageContent:
            data = self.parseOnePageContent(row['content'])
            self.statistics.append({
                'name':row['name'],
                'url':row['url'],
                'statictics':dict(**data['counter_info'], **self.getStatistics(data['weibo_list'])),
                'weibo_list':data['weibo_list']
            })
            #print(row['name'],row['url'],dict(**data['counter_info'], **self.getStatistics(data['weibo_list'])))

    def parseOnePageContent(self, content):
        result = {'counter_info':{}, 'weibo_list':[]}
        #print(content)
        page = etree.HTML(content)
        #粉丝数
        counterNode = page.xpath('//table[@class="tb_counter"]')
        #print(counterNode)
        if not counterNode:
            result['counter_info'] = {
                'attention' :0,
                'fans'      :0,
                'weibo'     :0    
            }
        else:
            attentionNode = counterNode[0].xpath('./tbody/tr/td[1]//strong')
            fansNode = counterNode[0].xpath('./tbody/tr/td[2]//strong')
            weiboNode = counterNode[0].xpath('./tbody/tr/td[3]//strong')
            result['counter_info'] = {
                'attention' :int(attentionNode[0].text) if attentionNode and attentionNode[0].text.isdigit() else 0,
                'fans'      :int(fansNode[0].text) if fansNode and fansNode[0].text.isdigit() else 0,
                'weibo'     :int(weiboNode[0].text) if weiboNode and weiboNode[0].text.isdigit() else 0,
            }

        #每条微博信息
        feedNodeList = page.xpath('//div[@action-type="feed_list_item"]')
        for feedNode in feedNodeList:
            contentNode = feedNode.xpath('.//div[@class="WB_detail"]/div[@node-type="feed_list_content"]')
            pubtimeNode = feedNode.xpath('.//div[@class="WB_detail"]/div[contains(@class,"WB_from")]/a[@node-type="feed_list_item_date"]/@title')
            forwardNode = feedNode.xpath('.//div[@class="WB_handle"]/ul/li[2]//span[contains(@class,"S_line1")]/span/em[2]')
            commentNode = feedNode.xpath('.//div[@class="WB_handle"]/ul/li[3]//span[contains(@class,"S_line1")]/span/em[2]')
            likeNode = feedNode.xpath('.//div[@class="WB_handle"]/ul/li[4]//span[contains(@class,"S_line1")]/span/em[2]')

            result['weibo_list'].append({
                'content':contentNode[0].text.strip() if contentNode else '',
                'pubtime':pubtimeNode[0],
                'forward':int(forwardNode[0].text) if forwardNode and forwardNode[0].text.isdigit() else 0,
                'comment':int(commentNode[0].text) if commentNode and commentNode[0].text.isdigit() else 0,
                'like':int(likeNode[0].text) if likeNode and likeNode[0].text.isdigit() else 0,
            })

        return result

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
        sheet = book.add_sheet('sheet1')
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
        for row in self.statistics:
            sheet.write(index, 0, row['name'])
            sheet.write(index, 1, row['url'])
            sheet.write(index, 2, row['statictics']['fans'])
            sheet.write(index, 3, row['statictics']['weibo'])
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

        #创建每个竞品的微博详细数据
        sheet2 = book.add_sheet('sheet2')
        headers2 = ['名称','主页','转发数','评论数','点赞数','发布时间','内容']
        for index2 in range(len(headers2)):
            sheet2.write(0, index2, headers2[index2])
        index = 1
        for row in self.statistics:
            for weibo in row['weibo_list']:
                columns = ['name','url','forward','comment','like','pubtime','content']
                for index2 in range(len(columns)):
                    if columns[index2] in ['name','url']:
                        sheet2.write(index, index2, row[columns[index2]])
                    else:
                        sheet2.write(index, index2, weibo[columns[index2]])
                index += 1
             
        book.save('weibo.xls')

parseWeibo = ParseWeibo()
parseWeibo.run()
