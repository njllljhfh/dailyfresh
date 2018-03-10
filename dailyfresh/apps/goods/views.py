from django.shortcuts import render

# Create your views here.
from django.template import loader
from django.views.generic import View
from goods.models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner


# 首页视图


class IndexView(View):

    def get(self, request):
        # 显示首页
        # 1.获取 全部商品分类 的数据
        categories = GoodsCategory.objects.all()
        # print(len(categories))
        # 2.获取 商品轮播图 的幻灯片
        banners = IndexGoodsBanner.objects.all()
        print(len(banners))
        # 3.获取 活动 的数据
        promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

        # 4.获取 全部商品分类 中的商品
        for category in categories:
            # 查询对应类别下的商品数据
            # display_type = 0, 是显示文字的数据
            # display_type = 1, 是显示图片的数据
            # 按照index排序 ,(如1234)
            # 等号左边的是字段名,右边的是for中的变量
            title_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0).order_by('index')
            # 将 title_banners 保存到 category对象的属性中
            category.title_banners = title_banners

            image_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1).order_by('index')
            # 将 image_banners 保存到 category对象的属性中
            category.image_banners = image_banners

        context = {
            'categories': categories,
            'banners': banners,
            'promotion_banners': promotion_banners,
        }

        # content 是数据渲染好的模板的最终的 html 代码
        content = loader.render_to_string('index.html', context)
        print(content)

        return render(request, 'index.html', context)
