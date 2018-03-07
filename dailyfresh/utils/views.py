from django.contrib.auth.decorators import login_required
from django.utils.decorators import classonlymethod


# 用来验证是否登录的类, 哪个视图需要认证,哪个视图继承
class LoginRequiredMixin(object):

    # django的装饰器
    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)

        return login_required(view)
