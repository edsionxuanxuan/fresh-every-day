
from django.urls import path, re_path
from . import views

app_name = 'goods'

urlpatterns = [
    path('index/', views.IndexView.as_view(), name='index'),
    re_path(r'^goods/(?P<goods_id>\d+)/$', views.DetailView.as_view(), name='detail'),
    re_path(r'^list/(?P<type_id>\d+)/(?P<page>\d+)/$', views.ListView.as_view(), name='list'),

]
