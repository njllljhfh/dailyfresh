from django.conf.urls import url

from orders import views

urlpatterns = [
    url(r'^place$', views.PlaceOrdereView.as_view(), name='place'),
    url(r'^commit$', views.CommitOrderView.as_view(), name='commit'),
    url('^(?P<page>\d+)$', views.UserOrdersView.as_view(), name="info"),  # 用户订单页面
    url('^pay$', views.PayView.as_view(), name="pay"),  # 支付
    url('^check_pay$', views.CheckPayStatusView.as_view(), name="check_pay"),  # 查询支付结果
    url('^comment/(?P<order_id>\d+)$', views.CommentView.as_view(), name="comment"),  # 评论
]
