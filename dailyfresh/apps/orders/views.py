import json

from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.utils import timezone
from django.views.generic import View
from django_redis import get_redis_connection

from goods.models import GoodsSKU
from orders.models import OrderInfo, OrderGoods
from users.models import Address
from utils.views import LoginRequiredMixin, LoginRequiredJsonMixin, TransactionAtomicMixin


class PlaceOrdereView(View):
    def post(self, request):
        """前端页面要传输 数据古来"""

        user = request.user

        # 1. 购物车点击 提交, 传过来 sku_ids
        # 2. 商品详情页面点击 立即购买 ,传过来 sku_ids 和 count
        # 注意 id有多个传过来获取要用getlist 如果用get只能获取到最后一个
        sku_ids = request.POST.getlist('sku_ids')

        # 只有从详情页面 点击 立即购买 才会传 count
        count = request.POST.get('count')

        # --------------
        if not user.is_authenticated():
            # 重定向到购物车
            response = redirect('/users/login?next=/cart')
            # 用户没有登录
            if count is not None:
                # 取出cookie里的数据
                cart_json = request.COOKIES.get('cart')
                # 如果cookie里有数据
                if cart_json:
                    cart_dict = json.loads(cart_json)
                else:
                    cart_dict = {}
                # {'id1':5,'id2':7}
                # 从立即购买页面进来 只有一个商品 取第0个
                sku_id = sku_ids[0]
                # 添加到字典里
                cart_dict[sku_id] = int(count)
                # 重定向到购物车
                if cart_dict:
                    response.set_cookie('cart', json.dumps(cart_dict))
            return response
        # ---------------

        # 校验参数
        if sku_ids is None:
            # 如果商品为空 ,去哪个页面,产品经理说的算
            return redirect(reverse('cart:info'))

        # 收货地址 有user能查到
        # 获取商品的sku对象 skus
        # 每种商品的数量
        # 每种商品的数量总价
        # 所有的商品的数量
        # 所有的商品的总价
        # 运费10
        # 所有的商品的总价包括运费

        # 收货地址(取最新的一个地址)
        try:
            # addr = Address.objects.filter(user=user).order_by('-create_time')[0]
            address = Address.objects.filter(user=user).latest('create_time')
        except Exception:
            # 如果没有地址,就是空,让用户去编辑收货地址
            address = None

        skus = []
        total_count = 0  # 所有的商品的数量
        total_sku_amount = 0  # 所有的商品的总价,不包括运费
        total_amount = 0  # 所有的商品的总价,包括运费
        trans_cost = 10  # 运费

        redis_conn = get_redis_connection('default')
        # {b'skuid1':b'10',b'skuid2':b'15'}
        cart_dict = redis_conn.hgetall('cart_%s' % user.id)

        if count is None:
            # 从购物车 跳转过来的

            for sku_id in sku_ids:
                try:
                    # 获取商品对象
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    return redirect(reverse('cart:info'))
                # 注意 sku_id 要进行编码,转化为字节型   1 --> b'1'
                sku_count = cart_dict.get(sku_id.encode())
                sku_count = int(sku_count)  # 当前遍历的商品的数量
                sku_amount = sku_count * sku.price  # 当前遍历的商品的小计
                sku.count = sku_count
                sku.amount = sku_amount
                total_count += sku_count  # 所有的商品的数量
                total_sku_amount += sku_amount  # 所有的商品的总价,不含运费
                # 保存全部的sku
                skus.append(sku)

        else:
            # 从购详情页 跳转过来的(其实只有一个商品,即 sku_ids 中只有一个元素)
            for sku_id in sku_ids:
                try:
                    # 获取商品对象
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    return redirect(reverse('cart:info'))
                # 通过网络传过来的 全是字符串,所有以要用 int() 对 count 进行转化
                try:
                    sku_count = int(count)
                except Exception:
                    # 如果商品数量有问题,返回到 该商品的 详情页面
                    return redirect(reverse('goods:detail', args=sku_id))

                # 判断库存
                if sku_count > sku.stock:
                    return redirect(reverse('goods:detail', args=sku_id))

                sku_amount = sku.price * sku_count  # 当前遍历商品的 小计

                # 把数据存到sku对象里
                sku.count = sku_count
                sku.amount = sku_amount
                total_count += sku_count  # 所有商品的数量
                total_sku_amount += sku_amount  # 所有商品的总价
                skus.append(sku)
                # 把当前商品加入到购物车字典里
                cart_dict[sku_id] = sku.count

            # 点击立即购买时,把商品添加到redis中(此时用户已经登录了)
            # 1可以在提交订单的时候 不管从哪个页面进来都可以查询数量(方便在CommitOrderView中使用 商品的count)
            # 2.如果用户把页面关掉 可以从购物车查询到
            redis_conn.hmset('cart_%s' % user.id, cart_dict)

        # 所有的商品的总价,包含运费
        total_amount = total_sku_amount + trans_cost

        print('sku_ids', sku_ids)  # sku_ids ['3', '1']
        context = {
            'skus': skus,
            'total_count': total_count,
            'total_sku_amount': total_sku_amount,
            'total_amount': total_amount,
            'trans_cost': trans_cost,
            'address': address,
            # sku_ids 是给 place_order.html 模板 中的 ajax请求上传数据是使用的
            'sku_ids': ','.join(sku_ids)  # ['1','2','3','4','5'] --> '1,2,3,4,5'
        }
        # 返回订单信息页面 注意还没有生成 提交后才生成
        return render(request, 'place_order.html', context)


# 提交订单的视图  验证用户有没有登录
# LoginRequiredJsonMixin,验证用户是否登录的类,在utils/views.py中
class CommitOrderView(LoginRequiredJsonMixin, TransactionAtomicMixin, View):
    # 有大量数据传过来 用于生成订单 用post ajax请求,ajax请求不能 重定向到其他页面

    def post(self, request):
        # 后端 只负责订单生成
        # 接收的参数  user 地址id 支付方式 商品id  数量
        user = request.user
        address_id = request.POST.get('address_id')  # 地址id
        pay_method = request.POST.get('pay_method')  # 支付方式
        # 前段ajax无法直接传过来数组列表 所以传过来一个字符串  '1, 2, 3, 4, 6'
        sku_ids = request.POST.get('sku_ids')  # 商品id  '1, 2, 3, 4, 6' split [1,2,3,4,6]

        # 校验参数
        print(111)
        if not all([address_id, pay_method, sku_ids]):
            return JsonResponse({'code': 1, 'msg': '参数不完整'})

        try:
            address = Address.objects.get(id=address_id)
            print(222)
        except Address.DoesNotExist:
            return JsonResponse({'code': 2, 'msg': '地址不存在'})

        if pay_method not in OrderInfo.PAY_METHOD:
            return JsonResponse({'code': 3, 'msg': '支付方式错误'})

        print(333)
        # 获取 redis 中的购物车数据
        redis_conn = get_redis_connection('default')
        # {b'skuid1':b'1',b'skuid2':b'7'....}
        redis_dict = redis_conn.hgetall('cart_%s' % user.id)

        # 订单号规则 20180315155959+userid
        # timezone 是 django下的工具
        # strftime 格式化时间的 字符串
        # 生成订单号
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 生成一个保存点 回滚用
        # 创建一个新的保存点。这将实现在事物里对“好”的状态做一个标记点。返回值是savepointID(sid).
        save_point = transaction.savepoint()

        try:
            # 生成订单表的实例对象(要在生成订单中的 具体的商品的表 之前 先生成 订单的实例对象)
            print(444)
            order = OrderInfo.objects.create(
                order_id=order_id,  # 订单号
                user=user,  # 用户
                address=address,  # 地址
                total_amount=0,  # 总价格（先设置为0，后面订单中的 具体商品表 生成后，计算可以得到总价格，再将这个属性更新）
                trans_cost=10,  # 运费
                pay_method=pay_method,  # 支付方式
            )
            total_count = 0  # 订单全部商品的总数量
            total_amount = 0  # 订单全部商品的总价格

            # 分割得到一个列表
            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                for i in range(3):
                    try:
                        # 获取商品对象
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        # 有异常 订单就不需要了 回滚 到save_point
                        transaction.savepoint_rollback(save_point)
                        return JsonResponse({'code': 4, 'msg': '支付方式错误'})
                    # 不要忘记sku_id 用 encode转为字节类型
                    sku_count = redis_dict.get(sku_id.encode())  # 从redis中获取当前商品的数量
                    # 强转
                    sku_count = int(sku_count)
                    # 判断库存数量
                    if sku_count > sku.stock:
                        # 有异常 订单就不需要了 回滚 到save_point
                        transaction.savepoint_rollback(save_point)
                        return JsonResponse({'code': 5, 'msg': '库存不足'})

                    # 当前真实库存 和之前的库存对比
                    # 保存之前查出来的库存
                    origin_stock = sku.stock  # 总量10个当前已经被a买走了5个 但是b之前查到的库存依然是10
                    new_stock = origin_stock - sku_count  # 购买成功后的 商品剩余库存
                    new_sales = sku.sales + sku_count  # 购买成功后的 商品的销量

                    # 更新成功 返回影响的行数 当前只有一个商品 成功返回1 不成功是0
                    # .update(要更新的字段=更新后的值) 跟mysql中的 update 类似
                    result = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                           sales=new_sales)

                    # 假设看库存10个，a买走了5个，  b要从剩余的5个中买3个
                    if result == 0 and i < 2:
                        # 给三次机会去数据库查库存
                        continue
                    elif result == 0 and i == 2:
                        # 第3次依然不成功 给用户一个响应  回滚
                        transaction.savepoint_rollback(save_point)
                        return JsonResponse({'code': 6, 'msg': '生成订单失败'})
                    break  # 如果第一次购买就成功了，直接跳出循环（即，result=1 and i=0）

                # 当前商品总价(即,小计)
                sku_amount = sku_count * sku.price
                total_count += sku_count  # 订单中，全部商品的总数量
                total_amount += sku_amount  # 订单中，全部商品的总价

                # 保存一个商品数据到订单商品表OrderGoods(订单中的 一个商品对应的表)
                # 在for循环中生成的 商品表, 都属是上面的订单表(order)中的商品
                OrderGoods.objects.create(
                    order=order,  # 当前商品属于的订单
                    sku=sku,  # 当前商品
                    count=sku_count,  # 当前商品的数量
                    price=sku_amount,  # 当前商品总价
                )

            # 循环结束后，把订单总数量和总价格 添加进数据库
            order.total_amount = total_amount + 10
            order.total_count = total_count
            order.save()
        except Exception:
            # 有异常 订单就不需要了 回滚 到save_point
            transaction.savepoint_rollback(save_point)
            return JsonResponse({'code': 6, 'msg': '生成订单失败'})

        # 事务提交
        transaction.savepoint_commit(save_point)

        # 订单生成后删除购物车(.hdel) 注意*sku_ids 解包(.hdel()的语法)
        redis_conn.hdel('cart_%s' % user.id, *sku_ids)

        # 成功或者失败 要去做什么 由前端来做
        return JsonResponse({'code': 0, 'msg': '提交成功'})


# 我的订单
class UserOrdersView(LoginRequiredMixin, View):
    """用户订单页面"""

    def get(self, request, page):
        user = request.user
        # 查询当前用户所有订单
        orders = user.orderinfo_set.all().order_by("-create_time")

        for order in orders:
            # 通过字典把数字对应的汉字取出来 存到对象里
            order.status_name = OrderInfo.ORDER_STATUS[order.status]
            order.pay_method_name = OrderInfo.PAY_METHODS[order.pay_method]
            order.skus = []
            order_skus = order.ordergoods_set.all()
            for order_sku in order_skus:
                sku = order_sku.sku
                sku.count = order_sku.count
                sku.amount = sku.price * sku.count
                order.skus.append(sku)
        # 分页
        page = int(page)
        try:
            paginator = Paginator(orders, 3)
            page_orders = paginator.page(page)
        except EmptyPage:
            # 如果传入的页数不存在，就默认给第1页
            page_orders = paginator.page(1)
            page = 1
        # 页数
        page_list = paginator.page_range

        context = {
            "orders": page_orders,
            "page": page,
            "page_list": page_list,
        }

        return render(request, "user_center_order.html", context)
