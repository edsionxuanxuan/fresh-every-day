import os
from celery import Celery

# 实例化对象
celery_app = Celery('dailyfresh')

# 把celery和django进行组合，必须让celery能识别和加载django的配置文件以及django的类库
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')

# 对django框架执行初始化
import django
django.setup()

# 加载配置
celery_app.config_from_object('celery_tasks.config')

# 注册任务
celery_app.autodiscover_tasks(['celery_tasks.email', 'celery_tasks.index_static'])