from functools import wraps

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.utils.decorators import classonlymethod


# 用来验证是否登录的类, 哪个视图需要认证,哪个视图继承
# 如果没有登录,会跳转到登录页面
class LoginRequiredMixin(object):

    # django的装饰器
    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)

        return login_required(view)


# --------------------------------------------------
# 提交订单的视图(CommitOrderView) 要用
# 定义一个装饰器 用来装饰视图函数 判断是否登录 如果没有登录返回json数据
def Login_Required_Json(view_func):
    # 恢复view_func的名字和文档,如果不加@wraps,那么被Login_Required_Json装饰后的函数的名字 会变成wrapper
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated():
            # 返回该 装饰器装饰的视图函数
            return view_func(request, *args, **kwargs)
        else:
            return JsonResponse({'code': 1, 'msg': '用户未登录'})

    return wrapper


# Login_Required_Json装饰器 只能装饰函数,所以要用一个类 来让其装饰 view函数
# 哪个视图需要认证,哪个视图继承
class LoginRequiredJsonMixin(object):
    @classonlymethod
    def as_view(cls, **initkwargs):
        # 调用父类的as_view
        view = super().as_view(**initkwargs)
        return Login_Required_Json(view)


# --------------------------------------------------

# 用来添加事务的类 需要的继承
class TransactionAtomicMixin(object):
    @classonlymethod
    def as_view(cls, **initkwargs):
        # 调用父类的as_view
        view = super().as_view(**initkwargs)
        return transaction.atomic(view)
