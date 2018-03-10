from django.contrib import admin

# Register your models here.
from goods.models import GoodsCategory, Goods, GoodsSKU, IndexGoodsBanner, IndexCategoryGoodsBanner, \
    IndexPromotionBanner
from celery_tasks.tasks import generate_static_index_html


class BaseAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """运营人员在admin界面中,添加或更新数据时会走的方法

        :param request: 请求对象
        :param obj: 运营人员更新或修改的 模型类的 实例化对象
        :param form: 传过来的原始表单数据
        :param change: 有两个值,表示是添加还是更新
        :return:
        """
        obj.save()
        # 数据一旦改变,就要生成新的index静态页面(celery,worker中的异步任务)
        generate_static_index_html.delay()

    def delete_model(self, request, obj):
        """运营人员在admin界面中,删除数据时会走的方法"""
        obj.delete()
        # 数据一旦改变,就要生成新的index静态页面(celery,worker中的异步任务)
        generate_static_index_html.delay()


# 运营人员对下列内容进行更改时,都要重新生成index.html的静态页面
class GoodsCategoryAdmin(BaseAdmin):
    pass


class GoodsAdmin(BaseAdmin):
    pass


class GoodsSKUAdmin(BaseAdmin):
    pass


class IndexGoodsBannerAdmin(BaseAdmin):
    pass


class IndexCategoryGoodsBannerAdmin(BaseAdmin):
    pass


class IndexPromotionBannerAdmin(BaseAdmin):
    pass


admin.site.register(GoodsCategory, GoodsCategoryAdmin)
admin.site.register(Goods, GoodsAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexCategoryGoodsBanner, IndexCategoryGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
