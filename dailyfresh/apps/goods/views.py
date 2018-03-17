import json

from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect

# Create your views here.
from django.template import loader
from django.views.generic import View
from django_redis import get_redis_connection

from goods.models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner, GoodsSKU


# 首页视图

class BaseCartView(View):
    """获取购物车数量的类"""

    def get_cart_num(self, request):
        cart_num = 0
        if request.user.is_authenticated():
            # 如果用户已登录,从redis中取购物车的数据
            # 购物车数据结构  登录后才能添加的  频繁访问存到redis
            # 每一个用户不一样 用redis的hash存储方便 cart_userid  ：  {'skuid1':'5','skuid2':'15','skuid3':'25'}
            # 获取购物车数量  每一个商品数量累加
            # 获取redis的链接实例
            redis_conn = get_redis_connection('default')
            # 获取request中的用户对象
            user = request.user
            # 获取购物车中,商品的数量 .hgetall() 得到一个字典  {'skuid1':'5','skuid2':'15','skuid3':'25'}
            cart_dict = redis_conn.hgetall('cart_%s' % user.id)
            # cart_dict.values() ---> [5, 15, 25]
        else:
            # 如果用户没有登录,从cookies中取购物车的数据
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                # 把 json 数据 转换为 dict
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}

        # 无论用户是否登录,都要对cart_dict.values() 进行遍历,获取所有商品的总数量
        for value in cart_dict.values():
            # 计算购物车中,所有商品的总数量
            # redis中所有的数据都是字符串
            cart_num += int(value)

        return cart_num


class IndexView(BaseCartView):

    def get(self, request):
        # 显示首页

        # 先从缓存中读取数据,如果有缓存数据,就获取缓存数据,反之,就执行查询
        context = cache.get('indexpage_static_cache')

        # 如果缓存不存在
        if context is None:
            print('缓存为空')
            # 1.获取 全部商品分类 的数据
            categories = GoodsCategory.objects.all()
            # print(len(categories))
            # 2.获取 商品轮播图 的幻灯片
            banners = IndexGoodsBanner.objects.all()
            # print(len(banners))
            # 3.获取 活动 的数据
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

            # 4.获取 全部商品分类 中的商品
            for category in categories:
                # 查询对应类别下的商品数据
                # display_type = 0, 是显示文字的数据
                # display_type = 1, 是显示图片的数据
                # 按照index排序 ,(如1234)
                # 等号左边的是字段名,右边的是for中的变量
                title_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0).order_by(
                    'index')
                # 将 title_banners 保存到 category对象的属性中
                category.title_banners = title_banners

                image_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1).order_by(
                    'index')
                # 将 image_banners 保存到 category对象的属性中
                category.image_banners = image_banners

            context = {
                'categories': categories,
                'banners': banners,
                'promotion_banners': promotion_banners,
            }
            # 把登录后的用户 在页面上相同的数据 保存到缓存中 不用每次都查找
            # settings 中的CACHE 就是设置的 缓存的存储
            # 设置缓存：cache.set('key', 内容, 有效期)
            cache.set('indexpage_static_cache', context, 3600)
        else:
            print('缓存不为空,直接使用了缓存中的数据')

        # content 是数据渲染好的模板的最终的 html 代码
        # content = loader.render_to_string('index.html', context)
        # print(content)

        # 购物车中商品的数量
        # 查询购物车信息：不能被缓存，因为会经常变化
        # 获取购物车数量的 代码 被提取到了 一个 类中(BaseCartView)
        cart_num = self.get_cart_num(request)

        # 补充购物车数据(不同的数据,要在缓存生成后,再添加到context中)
        context.update(cart_num=cart_num)

        return render(request, 'index.html', context)


class DetailView(BaseCartView):
    """显示商品详细信息页面"""

    # 商品分类信息
    # 商品sku信息
    # 商品spu信息（商品详情和其他规格的sku）
    # 新品推荐
    # 评论信息
    # 如果登陆 查询购物车
    def get(self, request, sku_id):
        # 尝试获取缓存数据
        context = cache.get("detail_%s" % sku_id)

        # 如果缓存不存在
        if context is None:
            try:
                # 获取商品信息
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                # from django.http import Http404
                # raise Http404("商品不存在!")
                return redirect(reverse("goods:index"))

            # 获取类别
            categories = GoodsCategory.objects.all()

            # 从订单中获取评论信息. 一个商品 可能存在于多个订单 要全部查出来
            sku_orders = sku.ordergoods_set.all().order_by('-create_time')[:30]
            if sku_orders:
                for sku_order in sku_orders:
                    # 将创建时间格式化后,保存在当前这个订单的 一个新的实例属性 中
                    # datetime.strftime 格式化时间
                    sku_order.ctime = sku_order.create_time.strftime('%Y-%m-%d %H:%M:%S')
                    # 当前订单商品 属于 哪个 用户
                    sku_order.username = sku_order.order.user.username
            else:
                sku_orders = []

            # 获取最新推荐
            new_skus = GoodsSKU.objects.filter(category=sku.category).order_by("-create_time")[:2]

            # 获取其他规格的商品(即,该spu 下的全部 sku,除了当前的sku)
            other_skus = sku.goods.goodssku_set.exclude(id=sku_id)

            context = {
                "categories": categories,
                "sku": sku,
                "orders": sku_orders,
                "new_skus": new_skus,  # 最新推荐商品
                "other_skus": other_skus
            }

            # 设置缓存
            cache.set("detail_%s" % sku_id, context, 3600)

        # 购物车数量
        # cart_num = 0
        cart_num = self.get_cart_num(request)

        # 如果是登录的用户
        if request.user.is_authenticated():
            # 获取用户id
            user = request.user
            # 从redis中获取购物车信息
            redis_conn = get_redis_connection("default")
            # 如果redis中不存在，会返回None
            # cart_dict = redis_conn.hgetall("cart_%s" % user.id)
            # for value in cart_dict.values():
            #     cart_num += int(value)
            # ----------------------------------------------------------

            # 浏览记录: lpush history_userid sku_1, sku_2
            # 商品添加到历史记录的数据结构 ‘history_userid’: [sku1.id, sku2.id, sku3.id, sku4.id, sku5.id]
            # 移除已经存在的本商品浏览记录(下面两行代码的作用,即,如果该商品存在于浏览记录中,则将该商品的浏览记录移动到最前面)
            # 第二个参数是 count    count>0   =0     <0
            redis_conn.lrem("history_%s" % user.id, 0, sku_id)
            # 添加新的浏览记录
            redis_conn.lpush("history_%s" % user.id, sku_id)
            # 只保存最多5条记录 ltrim截取前5个 其余的删了
            redis_conn.ltrim("history_%s" % user.id, 0, 4)

        context.update({"cart_num": cart_num})
        # context['cart_num'] = cart_num     与上一行代码功能一样

        return render(request, 'detail.html', context)


class ListView(BaseCartView):
    #  当前类别   水果
    #  排序 default
    #  当前的页码  1
    # url的设计 restfull
    # http://127.0.0.1:8000/goods/list/categoryid/1?sort=price
    # url(r'^list/(?P<category_id>\d+)/(?P<page>\d+)$', views.ListView.as_view(), name='list'),
    def get(self, request, category_id, page):
        """参数通过url传进来,是 str"""
        # 购物车
        # 当前类别
        # 所有的类别
        # 当前类别里所有的 商品
        # 新品推荐
        # 排序 默认default 价格price 人气hot
        # 分页的页码列表

        # 获取的排序
        sort = request.GET.get('sort')

        # 当前类别
        try:
            # category是该类别的实例对象
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            # 如果没有这个类别,去主页
            return redirect(reverse('goods:index'))

        # 所有的类别
        categories = GoodsCategory.objects.all()

        # 新品推荐(前两个)
        new_skus = GoodsSKU.objects.filter(category=category).order_by('-create_time')[0:2]

        # 当前类别里所有的 商品
        # 排序 默认default 价格price 人气hot
        if sort == 'price':
            skus = GoodsSKU.objects.filter(category=category).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(category=category).order_by('sales')
        else:
            # 除了上面两种以外,其他的sort都设为default(防止恶意用户篡改url中的数据)
            sort = 'default'
            skus = GoodsSKU.objects.filter(category=category)

        # 分页的页码列表(对全部商品进行分页)
        # 参1:要分页的对象, 参2:每页显示的数量
        paginator = Paginator(skus, 1)

        # 参数通过url传进来,是 str字符串,所以要转换成 int 类型
        # page是正则匹配进来的,所以一定是一个数字,不需要try来捕获异常
        page = int(page)

        # 获取当前页面的数据(skus_page当前页面对象)
        try:
            skus_page = paginator.page(page)
        # 防止恶意用户传入的页面不存在, 去第 1 页, 这个异常要导包
        except EmptyPage:
            page = 1
            skus_page = paginator.page(page)

        # 获取页码列表  要写到 EmptyPage异常处理之后  page才是正确的数据
        # 分页
        if paginator.num_pages <= 5:
            # 总页数小于 5 页(num_pages 和 page_range是paginator的属性)
            page_list = paginator.page_range
        elif page <= 3:
            # 当前页 page <= 3
            page_list = range(1, 6)
        elif paginator.num_pages - page <= 2:
            # 当前页为 后3页
            page_list = range(paginator.num_pages - 4, paginator.num_pages + 1)
        else:
            # 当前页为以上三种情况以外的情况
            page_list = range(page - 2, page + 3)

        context = {
            'sort': sort,
            'category': category,
            'categories': categories,
            'new_skus': new_skus,
            'skus': skus,
            'skus_page': skus_page,
            'page_list': page_list,
        }

        # 购物车数量
        cart_num = self.get_cart_num(request)

        # # 如果是登录的用户
        # if request.user.is_authenticated():
        #     # 获取用户id
        #     user = request.user
        #     # 从redis中获取购物车信息
        #     redis_conn = get_redis_connection("default")
        #     # 如果redis中不存在，会返回None
        #     cart_dict = redis_conn.hgetall("cart_%s" % user.id)
        #     for value in cart_dict.values():
        #         cart_num += int(value)

        context['cart_num'] = cart_num

        return render(request, 'list.html', context)
