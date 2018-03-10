from django.conf import settings
from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client


class FastDFSStorage(Storage):
    def _open(self):
        # 访问文件的时候
        pass

    # Django必须能够不带任何参数来实例化你的储存类。
    def __init__(self, client_conf=None, server_ip=None):
        if client_conf is None:
            # 如果使用者 没有传配置文件 就使用默认的配置文件
            client_conf = settings.FDFS_CLIENT_CONF

        self.client_conf = client_conf

        if server_ip is None:
            # 如果使用者 没有nginx的ip地址 就使用默认的 nginx的ip地址
            server_ip = settings.SERVER_IP
        self.server_ip = server_ip

    # name 是图片的原始名字, content是图片对象, 读取文件用 content.read()
    def _save(self, name, content):
        # 存储图片会调用的方法
        # 把图片存到fastdfs
        # 生成fdfs客户端对象, 用来访问fdfs服务器
        client = Fdfs_client(self.client_conf)
        # 读取图片二进制信息
        file_date = content.read()
        # 上传图片到fastdfs服务器
        try:
            # 上传图片过程中,可能由于网络问题或者其他问题导致上传失败
            ret = client.upload_by_buffer(file_date)
            print(1111)
            # 返回值ret的内容结构如下:
            # {
            #     'Group name': 'group1',
            #     'Status': 'Upload successed.',  # 注意这有一个点
            #     'Remote file_id': 'group1/M00/00/00/wKjzh0_xaR63RExnAAAaDqbNk5E1398.py',
            #     'Uploaded size': '6.0KB',
            #     'Local file name': 'test',
            #     'Storage IP': '192.168.243.133'
            # }
        except Exception as e:
            print(e)
            # 抛出异常,让调用该工具的人员自行捕获并处理
            raise

        if ret.get('Status') == 'Upload successed.':
            print(22222)
            # 判断是否上传成功
            # 获取文件的真实名字(Remote file_id)
            file_id = ret.get('Remote file_id')
            return file_id  # 会将图片的路径保存到 商品SKU表的 default_image 字段
        else:
            # 抛出异常,让调用该工具的人员自行捕获并处理
            raise Exception('上传图片到fdfs出现问题了')

    def exists(self, name):
        """定义实现existe()方法，返回False
            由于Djnago不存储图片，所以永远返回Fasle，直接引导到FastDFS"""
        return False

    def url(self, name):
        """返回能够访问到图片的完整地址"""
        # name :  group1/M00/00/00/wKjzh0_xaR63RExnAAAaDqbNk5E1398.py
        # 要拼接成完整的 路径 并 返回
        # http://192.168.1.136:8888/group1/M00/00/00/wKjzh0_xaR63RExnAAAaDqbNk5E1398.py

        # < img src = "{{ sku.default_image.url }}" >

        return self.server_ip + name
