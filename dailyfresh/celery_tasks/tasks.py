import os

# 添加环境变量(把一个东西添加到环境变量中, 那么在任何文件夹下都能执行
os.environ["DJANGO_SETTINGS_MODULE"] = "dailyfresh.settings"

# 放到Celery服务器上时 添加的代码(即woker)
import django

django.setup()  # 会把指定的路径下的  settings  的配置全部加载下来(这样在worker上就可以执行borker中的任务了.

from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

# 实例化Celery对象
# 参1:生成任务的文件 的 路径.  参2: broker的redis地址   redis://:密码@ip:port/数据库号
app = Celery('celery.tasks', broker='redis://192.168.21.134:6379/3')


# 发送邮件的 方法(这个不是视图)
# 使用装饰器 让方法 变成 celery的broker中的任务
@app.task
def send_mail_method(recipient_list, user_name, token):
    # 参1:邮件标题
    # 参2:邮件中的文本内容(message只能传入纯文本内容)
    # 参3:邮件发送方
    # 参4:邮件接收方(recipient_list,可以是多个人接收)
    # html_message, 可传能被浏览器渲染的标签的文本信息
    # send_mail(subject, message, from_email, recipient_list)
    # html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
    #             '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
    #             'http://127.0.0.1:8000/users/active/%s</a></p>' % (user_name, token, token)
    # send_mail('天天生鲜激活', '', settings.EMAIL_FROM, recipient_list, html_message=html_body)
    pass
