from django.conf.urls import url

from cart import views

urlpatterns = [
    url(r'^add/$', views.AddCartView.as_view(), name='add'),  # 添加购物车
    url(r'^$', views.CartInfoView.as_view(), name='info'),  # 购物车详情页
    url(r'^update$', views.UpdateCartView.as_view(), name='update'),  # 更新购物车数据
    url(r'^delete$', views.DeleteCartView.as_view(), name='delete'),  # 删除购物车数据
]
