# 自定义文件存储类
from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FDFSStorage(Storage):
    def __init__(self,  client_conf=None, base_url=None):
        """初始化传参"""
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url is None:
            base_url = settings.FDFS_BASE_URL
        self.base_url = base_url

    """fast dfs文件存储类"""
    def _open(self, name, mode='rb'):
        """打开文件时 使用"""
        pass

    def _save(self, name, content):
        """
        保存文件时使用
        :param name: 你选择的上传文件名字
        :param content: 包含你上传文件内容的File对象
        :return: 返回字典格式
        """
        # 创建一个fdfs_client对象
        client = Fdfs_client(self.client_conf)

        # 上传文件到fast dfs系统中
        res = client.upload_by_buffer(content.read())
        """
        {
        'Group name'      : group_name,
        'Remote file_id'  : remote_file_id,
        'Status'          : 'Upload successed.',
        'Local file name' : '',
        'Uploaded size'   : upload_size,
        'Storage IP'      : storage_ip
        }
        """
        if res.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception('上传文件到fastdfs失败')
        # 获取返回的文件ID
        file_name = res.get('Remote file_id')

        return file_name

    def exists(self, name):
        """django判断文件名是否可用
        因为django这边无法判断文件名，所以我们直接返回False
        """
        return False

    def url(self, name):
        """返回访问文件url路径"""
        return self.base_url + name