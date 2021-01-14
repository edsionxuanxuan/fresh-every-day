from django.contrib import admin
from django.core.cache import cache
from .models import GoodsImage,GoodsType, IndexPromotionBanner, IndexGoodsBanner, IndexTypeGoodsBanner,GoodsSKU


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """新增或更新表中数据时调用"""
        super().save_model(request, obj, form, change)
        # 重新发出任务，让celery worker重新生成首页静态页面
        from celery_tasks.index_static.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页的缓存数据
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        """删除表中数据时调用"""
        super().delete_model(request, obj)
        # 重新发出任务，让celery worker重新生成首页静态页面
        from celery_tasks.index_static.tasks import generate_static_index_html
        generate_static_index_html.delay()
        # 清除首页的缓存数据
        cache.delete('index_page_data')

class GoodsTypeAdmin(BaseModelAdmin):
    pass


class IndexPromotionBannerAdmin(BaseModelAdmin):
    pass


class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass


class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass

class GoodsImageAdmin(BaseModelAdmin):
    pass

class GoodsSKUAdmin(BaseModelAdmin):
    pass

admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(IndexGoodsBanner, IndexPromotionBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexPromotionBannerAdmin)
admin.site.register(GoodsImage, GoodsImageAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)