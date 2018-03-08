from django.contrib import admin

# Register your models here.
from goods.models import GoodsCategory, Goods, GoodsSKU

admin.site.register(GoodsCategory)
admin.site.register(Goods)
admin.site.register(GoodsSKU)
