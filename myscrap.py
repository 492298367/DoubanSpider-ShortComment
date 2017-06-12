# -*- coding: UTF-8 -*-  
import urllib2
import requests
from bs4 import BeautifulSoup
import re
from urllib import quote
import time
import sys
from pandas import Series,DataFrame
import pandas as pd 
import numpy as np
import xlwt

reload(sys)
sys.setdefaultencoding("utf-8") 

headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Referer':'https://accounts.douban.com/login?alias=&redir=https%3A%2F%2Fwww.douban.com%2F&source=index_nav&error=1001'

}

session = requests.Session()
session.headers.update(headers)


def getComment(url):
	#解析网址
	url = url_init(url)
	login(redir = url)
	message = session.get(url,headers = headers)
	names = re.findall('<title>(.*?)</title>',message.content)
	print "指定的爬取任务是%s"%names[0]

	pattern = '<div class="avatar">[\s\S]*?</p>'
	blocks = re.findall(pattern,message.content)

	#获得短评总数
	pattern = "<li class=\"is-active\">[\s\S]*?<span>.......(.*?).</span>"
	total_number = re.findall(pattern,message.content)
	total_number = int(total_number[0])


	#创建excel表格用于收集信息
	wb = xlwt.Workbook()
	ws = wb.add_sheet('A test sheet')
	ws.write(0,0,"index")
	ws.write(0,1,u'用户名')
	ws.write(0,2,u'时间')
	ws.write(0,3,u'评级')
	ws.write(0,4,u'支持数')
	ws.write(0,5,u'评论内容')

	i=0
	while i <= total_number:
		tgturl = turnPage(url,i)
		comment_blocks(tgturl,i,wb,ws)
		print "已完成%d条评论爬取，剩余%d条未爬取"%(i,total_number-i)
		i += 20


def url_init(short_comment_url):
	pattern = "(https://movie.douban.com/subject/.*?/comments\?)"
	tgt = re.findall(pattern,short_comment_url)
	return tgt[0]+"start=0&limit=20&sort=new_score&status=P"
	
def turnPage(short_comment_url,start_number):
	pattern1 = ".*?start="
	tgt = re.findall(pattern1,short_comment_url)
	return tgt[0]+"%d"%start_number+"&limit=20&sort=new_score&status=P"

def login(source='index_nav',redir='https://www.douban.com/',login='登录'):     #模拟登入函数
    username = raw_input('请输入你的用户名：')
    password = raw_input('请输入你的密码：')
    url = 'https://accounts.douban.com/login'
    caprcha_id,caprcha_link = get_captcha(url)          #把get_captcha函数返回的值
    if caprcha_id:          #如果有caprcha_id,就执行解析caprcha_link网页信息，并把图片保存下来打开
        print caprcha_link
        caprcha = raw_input('请输入验证码：')      #把看到的验证码图片输入进去
    data = {                    #需要传去的数据
        'redir':redir,
        'source':source,
        'redir':redir,
        'form_email':username,
        'form_password':password,
        'login':login,
    }
    if caprcha_id:          #如果需要验证码就把下面的两个数据加入到data里面
        data['captcha-id'] = caprcha_id
        data['captcha-solution'] = caprcha
    html = session.post(url,data=data,headers=headers)
    if html.url==redir:
        print "已成功登陆豆瓣，开始爬取指定电影短评"
    else:
        print "现在似乎无法登录，请重新尝试ORZ..."

def get_captcha(url):       #解析登入界面，获取caprcha_id和caprcha_link
    html = session.get(url)
    soup = BeautifulSoup(html.text,'lxml')
    check = ''
    caprcha_id = ''
    caprcha_link = ''

    if len(soup.select('div.captcha_block > input')) != 0:
            caprcha_id = soup.select('div.captcha_block > input')[1]['value']
            caprcha_link = soup.select('#captcha_image')[0]['src']
            print "需要验证码，请将在浏览器输入以下链接并跳转，输入途中验证码"
    #lzform > div.item.item-captcha > div > div > input[type="hidden"]:nth-child(3)
    return caprcha_id,caprcha_link
    

def comment_blocks(url,start_number,wb,ws):

	message = session.get(url, headers = headers)
	pattern = '<div class="avatar">[\s\S]*?</p>'
	blocks = re.findall(pattern,message.content)

	for i in xrange(0,len(blocks)):
		commentPage(start_number+i+1,blocks[i],wb,ws)

	wb.save('Results')
	time.sleep(3)

def commentPage(index,blocks,wb,ws):
	user_result = []
	time_result = []
	rates_result = []
	votes_result = []
	comment_result = []
	#统计用户名
	pattern = '<a href="https://www.douban.com/people/.*/" class="">'+'.*?'.encode("GBK")+'</a>'
	user = re.findall(pattern, blocks)
	soup = BeautifulSoup(user[0],"html.parser")
	user_result.append(soup.get_text())

	
	#评论发表时间
	pattern = '''<span class="comment-time " title=".*">
                    .*?
                </span>'''
	Timetag = re.findall(pattern,blocks)
	soup = BeautifulSoup(Timetag[0],"html.parser")
	time_result.append(soup.get_text().strip())

    #评价等级
	rates = re.findall('<span class=".*?rating" title=(.*?)></span>',blocks)
	if len(rates) == 0:
		rates = 'NA'
	soup = BeautifulSoup(rates[0],"html.parser")
	rates_result.append(soup.get_text())


    #支持数量
	votes = re.findall('<span class="votes">(.*?)</span>',blocks)
	soup = BeautifulSoup(votes[0],"html.parser")
	votes_result.append(soup.get_text())



	#评论收集
	pattern = """</h3>[\s\S]*?<p class="">([\s\S]*?)</p>"""
	comment = re.findall(pattern,blocks)
	soup = BeautifulSoup(comment[0],"html.parser")
	comment_result.append(soup.get_text().strip())

	#写入excel
	ws.write(index,1,user_result[0])
	ws.write(index,2,time_result[0])
	ws.write(index,3,rates_result[0])
	ws.write(index,4,votes_result[0])
	ws.write(index,5,comment_result[0])


url = raw_input(">>>>>>>>>")
getComment(url)



