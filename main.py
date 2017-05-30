import requests
import regex as re
import time
import random
import pymongo

class spider():

    def start(self,start_time, end_time, debug=False):
        url = "http://m.mayi.com"
        sum = 0 #统计爬虫爬取所有城市数据
        rooms_id = set()
        if debug == False:
            for city_id in self.getcity():
                time.sleep(2+random.random())
                print("爬取"+city_id['namechinese']+"信息")
                for offset_id in range(1,1000):
                    list = self.getpage(url,offset_id,city_id['nameenglish'],start,end)
                    if len(list)!=0:
                        for room_id in list:
                            rooms_id.add(int(room_id['id']))
                    else:
                        print("爬取完成," + city_id['namechinese'] +'爬取共' + str(len(rooms_id)))
                        sum+=len(rooms_id)
                        break
                print(self.url_manager(rooms_id, start))

        elif debug == True:
            city_id ={
                'namechinese':'北京',
                'nameenglish':'beijing'
            }
            print("爬取" + city_id['namechinese'] + "信息")
            for offset_id in range(1, 2):
                list = self.getpage(url, offset_id, city_id['nameenglish'], start, end)
                # print(list)
                while len(list) != 0:
                    page = list.pop()
                    room_id = page['id']
                    rooms_id.add(room_id)
            print("爬取完成," + city_id['namechinese'] + '爬取共' + str(len(rooms_id)))
            sum += len(rooms_id)
            all_datas = self.url_manager(rooms_id, start)
            self.filesaver(all_datas)

    def getcity(self):#获取城市信息,以便获取城市id并构造url
        allcity = requests.get('http://www.mayi.com/wap/getListOfOpenAndHot/').json()['opencitys']
        return allcity  #返回结果是list

    def getpage(self,url,offset_id,city,start_time,end_time):#获取房间信息
        ajax = "http://m.mayi.com/ajax/searchmore/"
        data = {
                    "offset":str(offset_id),#模拟翻页效果
                    "query_str":city, #由getcity函数得到城市id
                    "d1":start_time,  #住房起始时间
                    "d2":end_time   #住房结束时间
                }
        s = requests.Session()
        # user_agent = [
        #     "Mozilla/5.0 (Linux; Android 6.0.1; ONEPLUS A3000 Build/MMB29M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 Mobile Safari/537.36",  ##OnePlus 6.0.1 Chrome
        #     "Mozilla/5.0 (Linux; U; Android 5.0.2; zh-CN; Letv X501 Build/DBXCNOP5501304131S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 UCBrowser/10.10.0.800 U3/0.8.0 Mobile Safari/534.30",  ##乐视X501 UC浏览器
        #     "Mozilla/5.0 (Linux; U; Android 5.0.2; zh-cn; Letv X501 Build/DBXCNOP5501304131S) AppleWebKit/537.36 (KHTML, like Gecko)Version/4.0 Chrome/37.0.0.0 MQQBrowser/6.7 Mobile Safari/537.36",  ##乐视X501 Chrome浏览器
        #     "Mozilla/5.0 (Linux; Android 5.1.1; vivo X6S A Build/LMY47V) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/35.0.1916.138 Mobile Safari/537.36 T7/6.3 baiduboxapp/7.3.1 (Baidu; P1 5.1.1)",  ##vivo X6S 百度浏览器
        #     "Mozilla/5.0 (Linux; Android 4.4.4; HM 2A Build/KTU84Q) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/37.0.0.0 Mobile MQQBrowser/6.2 TBS/036215 Safari/537.36 V1_AND_SQ_6.3.1_350_YYB_D QQ/6.3.1.2735 NetType/4G WebP/0.3.0 Pixel/720"
        # ##红米手机2A 手机端QQ中直接打开（带4G标示）
        # ]
        headers = {
                    'user-agent': "Mozilla/5.0 (Linux; Android 6.0.1; ONEPLUS A3000 Build/MMB29M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 Mobile Safari/537.36",
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    # 'Accept-Encoding':'gzip'    #启用gzip压缩
                   }    #构造头部
        list = s.post(ajax,data=data,headers=headers)   #post数据，返回list
        rooms_id = list.json()['data']            #获取该城市中所有租房的room_id
        return rooms_id #返回结果是list

    def url_manager(self, rooms_id, start): #构造租房url并处理分析
        waiting = rooms_id  #带爬取队列
        finished = set()    #已完成队列
        details = []    #爬取结果，包含某城市所有房间信息
        while(len(waiting)!=0):     #爬取队列不为空时进行分析
            id = waiting.pop()
            detail = self.parse(id, start)
            finished.add(id)
            details.append(detail)
        return details  #返回一个list，包含该城市所有房源信息

    def parse(self, room_id, start): #页面分析，该函数需要单个租房room_id以及起始时间
        # start_time = time.time()  #性能分析
        detail = []
        info = {}
        RoomPage = 'http://www.mayi.com/room/'+str(room_id)
        getPraceUrl = 'http://www.mayi.com/room/getPrice' ##POST roomid=850059803&startDate=2017-5-01
        s = requests.Session()
        headers = {
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            # 'Accept-Encoding':'gzip'    #启用gzip压缩
        }
        data = {
            "roomid":str(room_id),
            "startDate":start
        }
        getPrace = s.post(getPraceUrl, data=data, headers=headers)
        detail.append(getPrace.json())

        content = s.get(RoomPage,headers=headers).text
        room_title = re.compile(r'(?<=<h2><a href="#" rel="nofollow">).*(?=</a>)')
        room_location = re.compile(r'(?<=<p>).*(?=<a rel = "nofollow" href="javascript:;" class=\'look_map\'>)')
        room_type = re.compile(r'(?<=<p>).*(?=</p>\s+?</li>\s+?<li class="w258">)')
        room_max = re.compile(r'(?<=ruzhu.png" class=\'fl\'/>\s+<span class=\'fl\'>).*(?=</span>)')
        room_bed = re.compile(r'(?<=\t{3}\s{12}\t{2}\s{5}).*(?=·)')
        room_introduce = re.compile(r'(?<=<div class=\'room_he\'>\r)([\w\W]*?)(?=</div)')
        room_location_detail = re.compile(r'(?<=<h4>地理位置</h4>\s+<p class="huan">\r\n\t{7}\s{17})([\w\W]*?)(?=<br>\s+</p>)')
        room_transport = re.compile(r'(?<=<h4>交通情况</h4>\s+<p class="huan">\r\n\t{7}\s{16})([\w\W]*?)(?=<br>\s+</p>)')
        room_around = re.compile(r'(?<=<h4>周边情况</h4>\s+<p class="huan">\r\n\t{7}\s{16})([\w\W]*?)(?=<br>\s+</p>)')
        room_rules = re.compile(r'(?<=<h4>房客守则</h4>\s+<p class="huan">\r\n\t{7}\s{16})([\w\W]*?)(?=<br>\s+</p>)')
        room_others = re.compile(r'(?<=<h4>其他</h4>\s+<p class="huan">\r\n\t{7}\s{16})([\w\W]*?)(?=<br>\s+</p>)')
        room_owner = re.compile(r'(?<=<div class="landlordDesR">\r\n\t{4}\s{16}\t<font>).*(?=</font>)')
        if len(re.findall(room_title, content)) != 0:
            info['room_title'] = re.findall(room_title, content)[0]
        if len(re.findall(room_location, content)) != 0:
            info['room_location'] = re.findall(room_location, content)[0]
        if len(re.findall(room_type, content)) != 0:
            info['room_type'] = re.findall(room_type, content)[0]
        if len(re.findall(room_max, content)) != 0:
            info['room_max'] = re.findall(room_max, content)[0]
        if len(re.findall(room_bed, content)) != 0:
            info['room_bed'] = re.findall(room_bed, content)[0]
        if len(re.findall(room_introduce, content)) != 0:
            info['room_introduce'] = re.findall(room_introduce, content)[0]
        if len(re.findall(room_location_detail, content))!=0:
            info['room_location_detail'] = re.findall(room_location_detail, content)[0]
        if len(re.findall(room_transport, content))!= 0:
            info['room_transport'] = re.findall(room_transport, content)[0]
        if len(re.findall(room_around, content)) != 0:
            info['room_around'] = re.findall(room_around, content)[0]
        if len(re.findall(room_rules, content)) != 0:
            info['room_rules'] = re.findall(room_rules, content)[0]
        if len(re.findall(room_others, content)) != 0:
            info['room_others'] = re.findall(room_others, content)[0]
        if len(re.findall(room_owner, content)) != 0:
            info['room_owner'] = re.findall(room_owner, content)[0]
        # end_time = time.time()    #性能分析
        # print(end_time-start_time)    #性能分析
        return info  #返回值为字典，包含该房间所有信息

    def filesaver(self, all_details):
        client = pymongo.MongoClient('localhost',27017)
        db = client.db
        collection = db.collection
        while len(all_details)!=0:
            tmp = all_details.pop()
            print(tmp)
            # collection.insert(tmp)
        print('储存完成')


if __name__=='__main__':
#########生产模式########
    # start = input('输入起始时间，格式1999-05-12')
    # end = input('输入结束时间，格式同上')
    mayi = spider()
    # mayi.start(start, end)

#########开发模式########
    start = '2017-07-30'
    end = '2017-07-31'
    # print(mayi.parse(850642153,start))
    mayi.start(start, end, debug=True)
