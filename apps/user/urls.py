
from django.urls import path, re_path
from . import views

app_name = 'user'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'), # 注册
    re_path(r'^active/(?P<token>.*)/$', views.ActiveView.as_view(), name='active'),# 用户激活
    path('login/', views.LoginView.as_view(), name='login'), # 登陆
    path('logout/', views.LogoutView.as_view(), name='logout'), # 退出

    path('', views.UserInfoView.as_view(), name='user'),  #用户中心-信息
    re_path(r'^order/(?P<page>\d+)/$', views.UserOrderView.as_view(), name='order'),  #用户中心-订单
    path('address/', views.AddressView.as_view(), name='address'),  #用户中心-地址
]
