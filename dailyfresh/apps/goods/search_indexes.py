from haystack import indexes
from goods.models import GoodsSKU


# 类名是   表的模型类的名字+Index
class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    """建立索引时被使用的类"""
    # text 是索引字段名字, 一般都用这个名字,不要改
    # use_template使用模板来指定表里哪写字段需要添加索引
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        """从哪个表中查询"""
        return GoodsSKU

    def index_queryset(self, using=None):
        """返回要建立索引的数据"""
        return self.get_model().objects.all()
