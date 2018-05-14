"""dailyfresh URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
import haystack
from django.conf.urls import include, url
from django.contrib import admin

# URL正则匹配中，增加了命名空间，方便后续的反解析
# URL正则匹配中，register后面是否加/，根据公司需求而定
urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^users/', include('users.urls', namespace='users')),
    url(r'^tinymce/', include('tinymce.urls')),  # 富文本编辑器
    url(r'^search/', include('haystack.urls')),  # 搜索引擎
    url(r'^goods/', include('goods.urls', namespace='goods')),
    url(r'^cart/', include('cart.urls', namespace='cart')),
    url(r'^orders/', include('orders.urls', namespace='orders')),
]
