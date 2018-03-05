import re

from django import db
from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
# 注册视图
from django.views.generic import View

# def register(request):
#     """返回注册页面
#
#     :param request:
#     :return:
#     """
#     # 展示页面 get 请求
#     # 注册 post请求
#     if request.method == 'GET':
#         return render(request, 'register.html')
#     else:
#         # 执行注册逻辑
#         return HttpResponse('okpost')


# 注册的类视图
# django提供了各种功能的类视图可以继承 ListView DetailView FormView
# 如果django提供的 类视图不能满足需求,就自己定义 类视图(继承与View)
# 每种请求 分开,结构清晰
from users.models import User


class RegisterView(View):

    def get(self, request):
        """get 的名字是固定的"""
        return render(request, 'register.html')

    def post(self, request):
        """post 的名字是固定的"""
        # 获取传过来的数据
        username = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验数据
        # 判断是否为空，都不为空的执行
        if not all([username, pwd, email]):
            return redirect(reverse('users:register'))  # 重定向的反向解析

        # 判断邮箱 是否是 正确的邮箱格式
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式错误'})

        # checkbox 如果勾选  会传过来一个 on 的字符串
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '没有勾选协议'})

        # 保存到数据库 insert
        # user = User()
        # user.username = username
        # user.password = pwd
        # user.email = email
        # create_user 在创建用户的过程中,对密码进行加密(用 sha256 加密算法)
        """加密:  {密码 + asdfawefasdfasdfawef(用于混淆的乱码,专业名词叫--盐值) + 当前时间} 
        然后整体加密,这样即使加密之前的密码相同,加密后的结果也是不同的"""
        try:
            user = User.objects.create_user(username=username, email=email, password=pwd)
        except db.IntegrityError:
            return render(request, 'register.html', {'errmsg': '该用户名已经被注册'})

        # django 默认是激活的 不符合我们的需求
        user.is_active = False

        # 保存到数据库 即 insert
        user.save()

        # 生成token ,token中包含 user.id, 生成token的过程叫做 签名
        token = user.generate_active_token()

        # 用户成功注册后,就要给用户发送激活邮件
        # 接收邮件的人  可以有多个
        # recipient_list = [user.email]  应该写成个
        recipient_list = ['dragonax@163.com']  # 这里是为了测试方便,就把邮箱写成固定的了
        send_mail_method(recipient_list, user.username, token)

        # 给浏览器响应
        return HttpResponse('okpost注册逻辑')


class ActiveView(View):

    def get(self, request, token):
        return HttpResponse('ok')


# 发送邮件的 方法(这个不是视图)
def send_mail_method(recipient_list, user_name, token):
    # 参1:邮件标题
    # 参2:邮件中的文本内容(message只能传入纯文本内容)
    # 参3:邮件发送方
    # 参4:邮件接收方(recipient_list,可以是多个人接收)
    # html_message, 可传能被浏览器渲染的标签的文本信息
    # send_mail(subject, message, from_email, recipient_list)
    html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                'http://127.0.0.1:8000/users/active/%s</a></p>' % (user_name, token, token)
    send_mail('天天生鲜激活', '', settings.EMAIL_FROM, recipient_list, html_message=html_body)
