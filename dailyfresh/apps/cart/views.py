import json

from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic import View
from django_redis import get_redis_connection

from goods.models import GoodsSKU


# 如果没有登录 也可以添加购物车
# 登录后 把之前的购物车的数据 添加到登录的账户里

# 登录后的数据结构   cart_userid: {'skuid1':10,'skuid2':3 ....}

# 没登录的数据结构  cart: '{'skuid1':10,'skuid2':3 ....}' json
# 存到cookie  在登录后 把数据转到服务器redis,并存到当前登录的用户下
class AddCartView(View):

    def post(self, request):
        # 用户信息user
        user = request.user

        # 应该接收的数据 skuid  数量 count
        # 接收传来数据方法里的参数equest.GETrequest.POST
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # # 当前需求是,必须登录后才能添加购物车
        # if not user.is_authenticated():
        #     return JsonResponse({'code': 5, 'msg': '用户没有登录'})

        # 需求变动, 要求不登录也能添加购物车

        # 对数据校验(比如这个数据为空, 和这个数据乱传的清况, 通过判断和捕获异常的形式)
        if not all([sku_id, count]):
            return JsonResponse({'code': 1, 'msg': '参数不全'})
        # 验证商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 2, 'msg': '商品不存在'})

        # 验证商品数量
        try:
            count = int(count)
        except Exception as e:
            print(e)
            return JsonResponse({'code': 3, 'msg': '数量不对'})

        # 商品数量不能超过库存
        if count > sku.stock:
            # print('xxxx')
            return JsonResponse({'code': 4, 'msg': '商品库存不足'})

        # print(111)
        if user.is_authenticated():
            # 如果用户登录,把数据存到redis   cart_userid: {'skuid1':10,'skuid2':3 ....}
            # 获取redis的链接实例
            redis_conn = get_redis_connection('default')

            # 判断当前的商品在数据库中是否已经有 数量 存在
            # 获取当前商品的数量(origin_count,如果没有数据,返回的是None)
            origin_count = redis_conn.hget('cart_%s' % user.id, sku_id)

            # 如果存在, 最后保存的数量 = 之前的数量+当前的数量
            # 如果不存在, 最后保存的数量 = 当前的数量
            if origin_count is not None:
                count += int(origin_count)

            # 保存sku_id和count 到 redis中
            redis_conn.hset('cart_%s' % user.id, sku_id, count)
        else:
            #  用户未登录 存到cookie中

            # cart  ：  '{'skuid1':10,' skuid2':3 ....}'
            # 获取商品之前,在  cookie 中的数量
            # 如果用户之前就没操作过购物车 cart_json获取的结果就是None
            cart_json = request.COOKIES.get('cart')  # 得到的是 一个 字符串

            if cart_json is not None:
                # 如果之前有购物车的 cookies
                # 如果存在, 最后保存的数量 = 之前的数量+当前的数量
                # json字符串 = json.dumps(字典)
                # dict = json.loads(json字符串)
                # 将 json数据 转换成 dict数据

                cart_dict = json.loads(cart_json)
                # print('cart_dict===', cart_dict)  # cart_dict=== {'10': 7}
            else:
                # 如果之前没有购物车的 cookies
                # 如果不存在, 最后保存的数量 = 当前的数量
                cart_dict = {}

            # 判断当前商品的id是否存在于 cookies 中
            if sku_id in cart_dict:
                # 如果存在,获取当前商品在之前的cookies中的购物车数量
                origin_count = cart_dict.get(sku_id)

                # 把之前cookies中的 购物车数量 累加到 当前的数量上,得到购物车的总数
                count += origin_count

            # 在 cart_dict 中 更新前商品的购物车数量为 最终的总数量count
            cart_dict[sku_id] = count  # 这是当前所有的商品最新的并且要保存到 cookies 中的购物车数量的 数据(此时还没有保存到cookies)
            # print('cart_dict', cart_dict)

        # 购物车数量
        cart_num = 0

        # 如果是登录的用户,从redis中查询购物车数量
        if request.user.is_authenticated():
            # print(222)
            # 获取用户id
            user = request.user
            # 从redis中获取购物车信息
            redis_conn = get_redis_connection("default")
            # 如果redis中不存在，会返回None
            cart_dict = redis_conn.hgetall("cart_%s" % user.id)
        # else:
        #     # 如果用户没有登录,从cookies中查询购物车数量
        #     # 此时还没有更新cookies中的数据(即,没有执行 response.set_cookie('cart', cart_json) ),所以这里获取的还是之前的cookies
        #     cart_json = request.COOKIES.get('cart')
        #     cart_dict = json.loads(cart_json)

        # 不论用户是否登录,都要遍历 cart_dict 中的值,并且累加,得到购物车的总数量(要么是redis中的总数量,要么是cookies中的总数量)
        for value in cart_dict.values():
            cart_num += int(value)
        # print(333)

        # 生成cookies要用 Response
        response = JsonResponse({'code': 0, 'msg': '购物车数据添加成功', 'cart_num': cart_num})
        # print(444)

        # 如果用户没有登录,才会更新 cookies 中的 购物车的数据
        if not user.is_authenticated():
            # print(cart_dict)
            # 把字典 转换为 字符串
            cart_json = json.dumps(cart_dict)
            # print(555)

            # 将最新的 未登录状态下的购物车数量 保存到 cookies 中
            response.set_cookie('cart', cart_json)
            # print(666)

        # print(777)
        # {'code':3,'msg':'添加购物车失败'}   code 0 ：添加成功  代表状态码 一般0是成功
        return response


# 展示购物车页面
class CartInfoView(View):
    """展示购物车数据时，不需要客户端传递数据到服务器端，因为需要的数据可以从cookie或者redis中获取"""

    # 登录 在redis中查数据
    # 没登录 在cookies中查数据

    def get(self, request):
        user = request.user
        # 商品的 sku 对象
        # 单个商品的数量
        # 单个商品的总价
        # 全部商品的数量
        # 全部商品的价格

        if user.is_authenticated():
            # 登录 在redis 查数据库
            redis_conn = get_redis_connection('default')
            # 获取所有的数据  {b'skuid1'：b'5', b'skuid2':b'10' }
            cart_dict = redis_conn.hgetall('cart_%s' % user.id)
        else:
            # 没登录 在cookies中查数据
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}

        total_count = 0  # 全部商品的数量
        total_amount = 0  # 全部商品的总价
        skus = []  # 全部商品的sku对象
        # 遍历字典,取sku_id,count
        for sku_id, count in cart_dict.items():
            try:
                # 获取当前遍历的 sku_id 对应的 商品的 sku 对象
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                # 如果当前遍历的这个 skuid 没有,忽略他,继续取下一个j
                continue
            # 因为redis中存的是字符串
            count = int(count)  # 单个商品的数量
            amount = sku.price * count  # 单个商品的总价
            sku.count = count  # 把当前商品的数量,保存在当前商品对象的一个属性中
            sku.amount = amount  # 把当前单个商品的总价,保存在当前商品对象的一个属性中
            total_count += count  # 全部商品的数量
            total_amount += amount  # 全部商品的总价
            skus.append(sku)  # 全部商品的sku对象

        context = {
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
        }
        return render(request, 'cart.html', context)


class UpdateCartView(View):
    """更新购物车"""

    def post(self, request):
        # 更新的是哪个 sku 即 sku_id
        # 更新后的数量是多少 count
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        user = request.user
        # 对数据进行校验
        if not all([sku_id, count]):
            # 如果有参数为空
            return JsonResponse({'code': 1, 'msg': '参数不完整'})
        try:
            # 判断商品是否存在
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 2, 'msg': '商品不存在'})

        try:
            # 从前段传来的数据 是 字符串
            print('count==', count)
            count = int(count)
        except Exception as e:
            print(e)
            return JsonResponse({'code': 3, 'msg': '商品数量不正确'})

        # 判断 该商品的库存是否充足
        if count > sku.stock:
            return JsonResponse({'code': 4, 'msg': '库存不足'})

        # 判断 用户 是否 登录
        if user.is_authenticated():
            # 如果用户已登录更改redis
            redis_conn = get_redis_connection('default')
            # 更改对应sku_id的数量count
            redis_conn.hset('cart_%s' % user.id, sku_id, count)
            return JsonResponse({'code': 0, 'msg': '更新数量成功'})
        else:
            # 如果用户未登录更改cookies
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
            # 更改对应sku_id的商品的数量 sku
            cart_dict[sku_id] = count
            # 将 字典 转化为 json 数据
            cart_json = json.dumps(cart_dict)

            response = JsonResponse({'code': 0, 'msg': '更新数量成功'})

            # 更新 cookies 中的购物车数据
            response.set_cookie('cart', cart_json)

            return response


class DeleteCartView(View):
    """删除购物车中的商品"""

    def post(self, request):
        # 商品 sku_id
        sku_id = request.POST.get('sku_id')

        user = request.user

        # 校验
        if not sku_id:
            return JsonResponse({'code': 1, 'msg': '参数不对'})

        if user.is_authenticated():
            # 如果用户登录 从redis中删除数据
            redis_conn = get_redis_connection('default')
            # 删除该商品在redis中的数据
            redis_conn.hdel('cart_%s' % user.id, sku_id)
            return JsonResponse({'code': 0, 'msg': '商品删除成功'})
        else:
            # 如果用户没有登录,从cookies中删除数据
            cookies_json = request.COOKIES.get('cart')
            if cookies_json is not None:
                # 如果 cookies 不是空的
                cookies_dict = json.loads(cookies_json)
                # print(1111)
                # 如果id 在字典里
                if sku_id in cookies_dict:
                    # print(type(sku_id))
                    # 删除该商品在 从cookies中去除的字典 中的数据
                    # print(2222)
                    cookies_dict.pop(sku_id)
                    # print(cookies_dict)
                    response = JsonResponse({'code': 0, 'msg': '商品删除成功'})
                    # 删除 该商品后 要更新 cookies 中的数据
                    # 注意: 存cookies 时,要把 字典 转化为 字符串
                    response.set_cookie('cart', json.dumps(cookies_dict))
                    # 这里必须返回,否则用户未登录时,删除商品会失败
                    return response

            return JsonResponse({'code': 0, 'msg': 'cookies中的购物车是空的'})
