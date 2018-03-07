from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from users import views

urlpatterns = [
    url(r'^register$', views.RegisterView.as_view(), name='register'),  # as_view() 是一个类方法
    url(r'^active/(?P<token>.+)$', views.ActiveView.as_view(), name='active'),  # 激活
    url(r'^login$', views.LoginView.as_view(), name='login'),  # 登录
    url(r'^logout$', views.LogoutView.as_view(), name='logout'),  # 退出登录
    # url(r'^address$', views.AddressView.as_view(), name='address'),  # 收货地址

    # 把装饰器login_required直接以方法的方式使用, 把视图函数传进来
    # login_required()完成下面的事情：
    # 1.如果用户没有登入，则重定向到settings.LOGIN_URL，并将当前访问的绝对路径传递到查询字符串中。
    # 例如：/users/login?next=/users/address
    # 2.如果用户已经登入，则正常执行视图。视图的代码可以安全地假设用户已经登入。
    # url(r'^address$', login_required(views.AddressView.as_view()), name='address'),  # 收货地址

    url(r'^address$', views.AddressView.as_view(), name='address'),  # 收货地址
]
