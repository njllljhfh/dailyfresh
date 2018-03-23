# ------------------------------这些配置在worker中要使用,在此处(即非worker服务器)可以删除了
# 放到Celery服务器上时 添加的代码(即worker)
import os
# 添加环境变量(把一个东西添加到环境变量中, 那么在任何文件夹下都能执行)
# os.environ["DJANGO_SETTINGS_MODULE"] = "dailyfresh.settings"
# import django
# django.setup()  # 会把指定的路径下的  settings  的配置全部加载下来(这样在worker上就可以执行broker中的任务了.
# -------------------------------

# celery -A celery_tasks.tasks worker -l info  在worker服务器上,指定 生成任务的文件 的路径
# Tracker启动   sudo   /etc/init.d/fdfs_trackerd   start
# Storage启动   sudo   /etc/init.d/fdfs_storaged   start
# Nginx启动   sudo    /usr/local/nginx/sbin/nginx
# Nginx重启   sudo    /usr/local/nginx/sbin/nginx -s reload

from django.template import loader
from goods.models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner

from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

# 实例化Celery对象
# 参1:生成任务的文件 的 路径.  参2: broker的redis地址   redis://:密码@ip:port/数据库号
app = Celery('celery_tasks.tasks', broker='redis://192.168.21.134:6379/3')


@app.task
def send_mail_method(recipient_list, user_name, token):
    """发送邮件的 方法(这个不是视图)
       使用装饰器 让方法 变成 celery的broker中的任务"""
    # send_mail(subject, message, from_email, recipient_list)
    # 参1:邮件标题
    # 参2:邮件中的文本内容(message只能传入纯文本内容)
    # 参3:邮件发送方
    # 参4:邮件接收方(recipient_list,可以是多个人接收)
    # html_message, 可传能被浏览器渲染的标签的文本信息
    html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                'http://127.0.0.1:8000/users/active/%s</a></p>' % (user_name, token, token)
    send_mail('天天生鲜激活', '', settings.EMAIL_FROM, recipient_list, html_message=html_body)


@app.task
def generate_static_index_html():
    """生成 主页静态页面文件 的方法"""
    # 显示首页
    # 1.获取 全部商品分类 的数据
    categories = GoodsCategory.objects.all()
    # print(len(categories))

    # 2.获取 商品轮播图 的幻灯片
    banners = IndexGoodsBanner.objects.all()
    print(len(banners))

    # 3.获取 活动 的数据
    promotion_banners = IndexPromotionBanner.objects.all()

    # 4.获取 全部商品分类 中的商品
    for category in categories:
        # 查询对应类别下的商品数据
        # display_type = 0, 是显示文字的数据
        # display_type = 1, 是显示图片的数据
        # 按照index排序 ,(如1234)
        # 等号左边的是字段名,右边的是for中的变量
        title_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0).order_by('index')

        # 将 title_banners 保存到 category对象的属性中
        category.title_banners = title_banners

        image_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1).order_by('index')

        # 将 image_banners 保存到 category对象的属性中
        category.image_banners = image_banners

    context = {
        'categories': categories,
        'banners': banners,
        'promotion_banners': promotion_banners,
    }

    # content 是数据渲染好的模板的最终的 html 代码
    # static_index.html 是复制了一份 index.html,删除了登陆后相关的代码
    content = loader.render_to_string('static_index.html', context)
    # print(content)

    # 把content保存成 一个 静态文件
    # 获取要写入的文件的路径,存到 static 目录下 index.html
    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'index.html')

    # 把数据写入 static/index.html 文件中
    with open(file_path, 'w') as f:
        f.write(content)
