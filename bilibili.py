# -*-coding:utf-8 -*-
import requests, json, re, sys, os
from contextlib import closing

# 移除SSL认证警告
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


class spider:
    def __init__(self,keyword):
        # Requests Headers验证 防止反爬虫
        self.video_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}

        self.search_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'application/json, text/plain, */*'}

        self.dn_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://search.bilibili.com/all?keyword=%s' % keyword}
        self.sess = requests.session()

    # 获取视频下载地址
    def download_url(self, video_url):
        req = self.sess.get(url=video_url, headers=self.video_headers)
        # 正则获取
        pattern = '.__playinfo__=(.*)</script><script>window.__INITIAL_STATE__='
        infos = re.findall(pattern, req.text)[0]
        # json转换字典并提取地址
        html = json.loads(infos)
        durl = html['durl'][0]
        backup_url = durl['backup_url']
        url=durl['url']
        # 返回的是元组 分别是视频下载地址和备用地址
        return url,backup_url

    # 从API中提取数据
    def search_video(self, search_url):
        titles = []
        arcurls = []
        req = self.sess.get(url=search_url, headers=self.search_headers, verify=False)
        html = json.loads(req.text)
        videos = html["data"]['result']
        for video in videos:
            titles.append(video['title'].replace('<em class="keyword">', '').replace('</em>', ''))
            arcurls.append(video['arcurl'])
        # 返回标题序列和视频播放地址序列 一一对应
        return titles, arcurls

    # 主程序
    def search_videos(self, keyword, pages):
        for page in range(1, pages + 1):
            url_link = []
            search_url = 'https://api.bilibili.com/x/web-interface/search/type?jsonp=jsonp&search_type=video&keyword={}&page={}'.format(keyword, page)
            titles, arcurls = self.search_video(search_url)
            for index, arcurl in enumerate(arcurls):
                title = titles[index]
                print(index,title)
                # 写入操作 在当前目录下生成url.txt文件
                with open('url.txt', 'a',encoding='utf-8') as f:
                    f.write(title)
                    f.write('\n')
                    url_link.append(self.download_url(arcurl))
                    # url_link是元组序列 [(url,backup_url),]
                    f.write(url_link[-1][1][0])
                    f.write('\n')
            print('视频链接爬取完成\n')
            # 下载操作
            number=input('输入视频序号进行下载 无下载输入n：')
            while (number!='n'):
                self.video_downloader(url_link[int(number)][0], titles[int(number)])
                number = input('输入视频序号进行下载 无下载输入n：')

    # 视频下载(可选)
    def video_downloader(self, video_url, video_name):
        size = 0
        # 单线程下载
        with closing(self.sess.get(video_url, headers=self.dn_headers, stream=True, verify=False)) as response:
            chunk_size = 1024
            content_size = int(response.headers['content-length'])
            if response.status_code == 200:
                sys.stdout.write('  [文件大小]:%0.2f MB\n' % (content_size / chunk_size / 1024))
                with open(video_name+'.flv', 'wb') as file:
                    for data in response.iter_content(chunk_size=chunk_size):
                        file.write(data)
                        size += len(data)
                        file.flush()
                        sys.stdout.write('  [下载进度]:%.2f%%' % float(size / content_size * 100) + '\r')
                        # sys.stdout.flush()
                        if size / content_size == 1:
                            print('\n')
            else:
                print('链接异常')


if __name__ == '__main__':
    keyword = sys.argv[1]
    page = int(sys.argv[2])
    a = spider(keyword)
    a.search_videos(keyword, page)

