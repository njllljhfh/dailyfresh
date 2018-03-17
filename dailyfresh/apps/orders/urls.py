from django.conf.urls import url

from orders import views

urlpatterns = [
    url(r'^place$', views.PlaceOrdereView.as_view(), name='place'),
    url(r'^commit$', views.CommitOrderView.as_view(), name='commit'),
    url('^(?P<page>\d+)$', views.UserOrdersView.as_view(), name="info"),
]
