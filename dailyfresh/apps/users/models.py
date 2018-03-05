from django.db import models
from django.contrib.auth.models import AbstractUser

# from apps.goods.models import GoodsSKU
# from goods.models import GoodsSKU
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings

# Create your models here.
from utils.models import BaseModel


class User(AbstractUser, BaseModel):
    """用户"""

    class Meta:
        db_table = "df_users"

    def generate_active_token(self):
        """生成激活令牌"""
        # 参1:SECRET_KEY 盐值,  参2:3600 秒,过期时间
        serializer = Serializer(settings.SECRET_KEY, 3600)
        # {"confirm": self.id} 这是json数据
        # dumps 通过算法 把用户id转码,生成token
        token = serializer.dumps({"confirm": self.id})  # 返回bytes类型
        return token.decode()  # token 是 b'aasdfwefasdfasdfas' 这种形式,所以要用 decode 解码


class Address(BaseModel):
    """地址"""
    user = models.ForeignKey(User, verbose_name="所属用户")
    receiver_name = models.CharField(max_length=20, verbose_name="收件人")
    receiver_mobile = models.CharField(max_length=11, verbose_name="联系电话")
    detail_addr = models.CharField(max_length=256, verbose_name="详细地址")
    zip_code = models.CharField(max_length=6, verbose_name="邮政编码")

    class Meta:
        db_table = "df_address"
