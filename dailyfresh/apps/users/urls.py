from django.conf.urls import url

from users import views

urlpatterns = [
    url(r'^register$', views.RegisterView.as_view(), name='register'),  # as_view() 是一个类方法
    url(r'^active/(?P<token>.+)$', views.ActiveView.as_view(), name='active'),
]
