import os
from celery import Task
from django.shortcuts import render
from django.conf import settings
from celery_tasks.main import celery_app
from goods import models
from django.template import loader, RequestContext


# 监听整个任务的钩子
class Mytask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        print('task success 11111')
        return super(Mytask, self).on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print('task failed')
        # 可以记录到程序中或者任务队列中,让celery尝试重新执行
        return super(Mytask, self).on_failure(exc, task_id, args, kwargs, einfo)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        print('this is after return')
        return super(Mytask, self).after_return(status, retval, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        print('this is retry')
        return super(Mytask,self).on_retry(exc, task_id, args, kwargs, einfo)


@celery_app.task(name='generate_static_index_html', base=Mytask)
def generate_static_index_html():
    """产生首页静态页面"""
    # 获取商品的种类信息
    types = models.GoodsType.objects.all()

    # 获取首页轮播商品信息
    goods_banners = models.IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销活动信息
    promotion_banners = models.IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:
        # 获取type种类首页分类商品的图片展示信息
        image_banners = models.IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by()
        # 获取type种类首页分类商品的文字展示信息
        title_banners = models.IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by()

        # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
        type.image_banners = image_banners
        type.title_banners = title_banners


    # 组织模板上下文
    context = {
        'types': types,
        'goods_banners': goods_banners,
        'promotion_banners': promotion_banners,
    }
    # 使用模板
    # 1.加载模板文件
    temp = loader.get_template('static_index.html')
    # 2.模板渲染
    static_index_html = temp.render(context)
    # 生成首页对应静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)