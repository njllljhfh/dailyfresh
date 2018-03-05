import re

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
        """get的名字是固定的"""
        return render(request, 'register.html')

    def post(self, request):
        """post的名字是固定的"""
        # 获取传过来的数据
        username = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验数据
        # 判断是否为空，都不为空的执行
        if not all([username, pwd, email]):
            return redirect(reverse('users:register'))  # 重定向的反向解析

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
        user = User.objects.create_user(username=username, email=email, password=pwd)
        # 保存到数据库 即 insert
        user.save()

        # 给浏览器响应
        return HttpResponse('okpost注册逻辑')
