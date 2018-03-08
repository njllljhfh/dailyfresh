import re

import itsdangerous
from django import db
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import classonlymethod
from django.views.generic import View
from celery_tasks.tasks import send_mail_method
from goods.models import GoodsSKU
from users.models import User, Address

from utils.views import LoginRequiredMixin


# Create your views here.
# 注册视图

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

        # 通过delay调用 ,通知worker执行任务(tasks.py中的方法中的 代码可以不用写,保留方法就可以,worker中有对应的方法来执行代码)
        # 执行后有返回值(一串数字,例如:632111f - 0240 - 4c35 - bd9c - 060ca376db04),可保存在backend中(该数字在redis中保存为key)
        send_mail_method.delay(recipient_list, user.username, token)

        # 给浏览器响应
        return HttpResponse('okpost注册逻辑')


# ----------------------------------------------------------

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings


class ActiveView(View):

    def get(self, request, token):
        # 解析token,获取用户id信息
        # 参1: 混淆用的盐值 参2: 过期时间
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            # 解析token获取id信息,
            result = serializer.loads(token)  # 结果是: {"confirm": self.id} (users/models中的字典)
        # 激活令牌(token)过期,会捕获这个异常
        except itsdangerous.SignatureExpired:
            return HttpResponse('激活邮件已过期')

        # 在字典中提取 用户的id
        userid = result.get('confirm')

        # 根据用户id 获取用户
        try:
            user = User.objects.get(id=userid)
        # 模型中都封装有 DoesNotExist 这个异常(可用  模型类名.DoesNotExist  来捕获该异常)
        # 当 get 获取到的数据为 0 时,会捕获到这个异常(即说明该用户不存在)
        except User.DoesNotExist:
            return HttpResponse('该用户不存在')

        # 如果用户已经注册
        if user.is_active:
            return HttpResponse('该用户已经激活')

        # 注册用户
        user.is_active = True
        user.save()  # update

        # return HttpResponse('激活成功,去登录界面')
        # 激活成功后,跳转到 登录的界面
        return redirect(reverse('users:login'))


# ----------------------------------------------------------
# # 发送邮件的 方法(这个不是视图)
# def send_mail_method(recipient_list, user_name, token):
#     # 参1:邮件标题
#     # 参2:邮件中的文本内容(message只能传入纯文本内容)
#     # 参3:邮件发送方
#     # 参4:邮件接收方(recipient_list,可以是多个人接收)
#     # html_message, 可传能被浏览器渲染的标签的文本信息
#     # send_mail(subject, message, from_email, recipient_list)
#     html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
#                 '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
#                 'http://127.0.0.1:8000/users/active/%s</a></p>' % (user_name, token, token)
#     send_mail('天天生鲜激活', '', settings.EMAIL_FROM, recipient_list, html_message=html_body)


# 登录的类视图
class LoginView(View):
    # 进入登录页面
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # 1.接收数据
        username = request.POST.get('username')
        psw = request.POST.get('pwd')

        # 2.校验 用户输入的登录数据 是否为空
        if not all([username, psw]):
            # 如果有任意一个为空,则返回登录界面重新登录
            return redirect(reverse('users:login'))

        # 3.数据库获取用户
        # User.objects.filter(username=username, password=psw)
        # django提供的验证方法 authenticate,成功返回User对象, 不成功返回 None
        user = authenticate(username=username, password=psw)

        if user is None:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})

        # 4.判断用户是否激活
        if not user.is_active:
            # 如果没有激活,返回到登录界面
            return render(request, 'login.html', {'errmsg': '该用户未激活'})

        # 5.记住用户 功能
        # django提供的 用来保存用户信息 到session里 实现,比如十天不用登录等功能
        """
        如果你有一个认证了的用户，你想把它附带到当前的会话中 - 这可以通过login()函数完成。
        从视图中登入一个用户，请使用login()。它接受一个HttpRequest对象和一个User对象。
        login()使用Django的session框架来将用户的ID保存在session中。"""
        login(request, user)

        """
        如果value是一个整数，会话将在value秒没有活动后过期
        如果value为0，那么用户会话的Cookie将在用户的浏览器关闭时过期
        如果value为None，那么会话则两个星期后过期"""
        # 获取 用户是否在 登录界面勾选 <记住用户> 选项
        remembered = request.POST.get('remembered')

        # 将session存在redis中 , 在 settings 中配置

        if remembered != 'on':
            # 如果没勾选<记住用户> 则在关闭浏览器时, Cookie过期
            request.session.set_expiry(0)
        else:
            # 如果勾选了<记住用户> 则Cookie 保存2周
            request.session.set_expiry(None)

        # 6.如果之前是去用户相关的页面, 而重定向到登录页面的,
        # 那么登录以后就跳转到用户相关的界面
        # http://127.0.0.1:8000/users/login?next=/users/address
        # next=/users/address  跳转回哪个页面,根据next来确定
        next = request.GET.get('next')
        if next is None:
            # 去商品主页
            return HttpResponse('去商品主页')
        else:
            # 重定向到用户相关页面
            return redirect(next)


# 退出的类视图
class LogoutView(View):
    def get(self, request):
        # 清除登录信息
        """
        Django用户认证系统提供logout()函数
        参数：request
        说明：如果用户已登录，Django用户认证系统会把user对象加入到request当中
        结论：从request中可以获取到user信息，request.user"""
        logout(request)

        return redirect(reverse('users:login'))


# 收货地址视图
# 多继承,两个父类中有 同名的方法,谁在前面,执行谁的
class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        # 用户是否登录
        # request 有一个 user对象
        # 如果用户登录后 就是用户的User对象
        # 如果没有登录 user不是None 是AnonymousUser(匿名用户)的对象,这个对象没有用户信息
        """
        AnonymousUser(匿名用户),的一些特点:
        id---永远为None。
        username---永远为空字符串。
        is_active---永远为False。
        is_authenticated() 返回False"""
        # user = request.user
        # if not user.is_authenticated():
        #     # 如果没有登录,去登录页面进行登录
        #     return render(request, 'login.html')
        # ---------------------------------

        user = request.user
        # 排序获取最近添加的地址
        # user.address_set.order_by('-create_time')[0]
        # latest django的方法, 排序获取最近添加的地址,只会返回一个值
        try:
            # address 是一个地址模型类的实例对象
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None

        context = {
            # user不用传,request中自带user,调用模板时，request会传给模板
            # 'user': user,
            'address': address
        }
        return render(request, 'user_center_site.html', context)

    def post(self, request):
        """修改地址信息"""
        user = request.user
        recv_name = request.POST.get("recv_name")
        addr = request.POST.get("addr")
        zip_code = request.POST.get("zip_code")
        recv_mobile = request.POST.get("recv_mobile")
        print(11111111111111111)

        if all([recv_name, addr, zip_code, recv_mobile]):
            print(222222222222222)
            # address = Address(
            #     user=user,
            #     receiver_name=recv_name,
            #     detail_addr=addr,
            #     zip_code=zip_code,
            #     receiver_mobile=recv_mobile
            # )
            # address.save()

            # 创建好一个地址信息, 保存到数据库 insert
            Address.objects.create(
                user=user,
                receiver_name=recv_name,
                detail_addr=addr,
                zip_code=zip_code,
                receiver_mobile=recv_mobile
            )
            print(3333333333333333333)

        return redirect(reverse("users:address"))


from django_redis import get_redis_connection


# 用户信息页面
class UserInfoView(LoginRequiredMixin, View):

    def get(self, request):
        # 获取用户
        user = request.user

        # latest django的方法, 排序获取最近添加的地址,只会返回一个值
        try:
            # address 是一个地址模型类的实例对象
            address = request.user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None

        # 获取浏览记录
        # 存在redis中, string,列表,集合,有序集合,hash
        # 选择用列表存,结构是: 'history_userid': [sku1.id, sku2.id, sku3.id, sku4.id,]

        # 使用django-redis的原生客户端,连接redis缓存,建立redis连接的实例对象redis_conn
        redis_conn = get_redis_connection('default')

        # 获取reids列表中的数据  lrange  0  4, 获取的是某个用户的 前五个浏览记录商品的id(sku_id)
        sku_ids = redis_conn.lrange('history_%s' % user.id, 0, 4)

        # 去数据库查询具体数据
        # select * from df_goods_sku where id in
        # skus = GoodsSKU.objects.filter(id__in=sku_ids)
        # 上面这样 查询得到的数据的顺序 跟 sku_ids 中的顺序不同(如 redis中是:5,2,6,3,4   mysql 中是:2,3,4,5,6

        skus = []  # 存放商品对象的列表
        for sku_id in sku_ids:
            # 查询redis中获取的前五个商品的列表中的 每一个 sku
            sku = GoodsSKU.objects.get(id=sku_id)
            # 将查询到的 商品对象 添加到 skus 中
            skus.append(sku)

        context = {'address': address,
                   'skus': skus
                   }

        return render(request, 'user_center_info.html', context)
