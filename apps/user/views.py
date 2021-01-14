import re
from django_redis import get_redis_connection
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from goods.models import GoodsSKU
from user.models import User, Address
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from celery_tasks.email.tasks import send_verify_email
from django.contrib import auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from order.models import OrderGoods, OrderInfo
from django.core.paginator import Paginator


# /user/register/
class RegisterView(View):
    """注册视图类"""
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        repassword = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        # 校验协议勾选
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '协议未勾选'})
        # 校验用户名 是否重复
        exists = User.objects.filter(username=username).exists()
        if exists:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        # 两次密码校验
        if password != repassword:
            return render(request, 'register.html', {'errmsg': '两次密码不一致'})
        # 校验邮箱 是否重复
        exists = User.objects.filter(email=email).exists()
        if exists:
            return render(request, 'register.html', {'errmsg': '邮箱已存在'})
        # 进行业务处理
        user = User.objects.create_user(username=username, email=email, password=password)
        # 刚注册过的用户不应该是激活状态，所以要改成未激活
        user.is_active = 0
        user.save()

        #  发送激活邮件，包含激活链接：http://127.0.0.1:8000/user/active/3
        # 激活链接中需要包含用户的身份信息，并且要把身份信息进行加密处理
        # 加密用户的身份信息，生成激活的token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode('utf-8')

        # 调用celery任务
        send_verify_email.delay(username, token, email)

        # 返回应答 跳转到首页
        return redirect(reverse('goods:index'))


# /user/active/
class ActiveView(View):
    """用户激活视图类"""
    def get(self, request, token):
        # 进行解密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活用户id
            user_id = info['confirm']
            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 跳转到登陆页面
            return redirect(reverse('user:login'))
        except SignatureExpired:
            # 激活连接已过期
            return render(request, '404.html')


# /user/login/
class LoginView(View):
    """登录视图类"""
    def get(self, request):
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})
        # 登录校验
        try:
            user = auth.authenticate(username=username, password=password)
            if user.is_active: # 用户是否激活
                auth.login(request, user) # 相当于session

                # 获取登陆后要跳转的地址
                next_url = request.GET.get('next', reverse('goods:index'))
                # 判断是否需要记住用户名
                response = redirect(next_url)
                if remember == 'on':
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')
                return response
            else:
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        except Exception:
            return render(request, 'login.html', {'errmsg': '登录失败'})


# /user/logout/
class LogoutView(LoginRequiredMixin, View):
    """退出登陆"""
    def get(self, request):
        logout(request)
        return redirect(reverse('user:login'))


# /user/
class UserInfoView(LoginRequiredMixin, View):
    """用户中心-信息页"""
    def get(self, request):
        # 获取用户的个人信息
        try:
            address = Address.objects.get(user=request.user, is_default=True)
        except Address.DoesNotExist:
            # 不存在默认收货地址
            address = None
        # 获取用户的历史浏览记录
        conn = get_redis_connection('history')
        history_key = 'history_%d' % request.user.id
        # 获取用户最新浏览的5个商品信息
        sku_ids = conn.lrange(history_key, 0, 4)

        # 遍历获取用户浏览的历史商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文
        context = {
            'page': 'user',
            'address': address,
            'goods_li': goods_li
        }

        return render(request, 'user_center_info.html', context)


# /user/order/
class UserOrderView(LoginRequiredMixin, View):
    """用户中心-订单页"""
    def get(self, request, page):
        # 获取用户订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算是商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count*order_sku.price
                # 动态给order_sku增加属性amount，保存订单商品的小计
                order_sku.amount = amount

            # 动态给order增加属性.保存订单商品的信息
            order.order_skus = order_skus

        # 分页
        paginator = Paginator(orders, 1)
        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {
            'order_page': order_page,
            'pages': pages,
            'page': 'order'
        }
        # 使用模板
        return render(request, 'user_center_order.html', context)


# /user/address/
class AddressView(LoginRequiredMixin, View):
    """用户中心-地址页"""
    def get(self, request):
        # 获取用户的默认收货地址
        address_queryset = Address.objects.filter(user=request.user)
        return render(request, 'user_center_site.html', {'page': 'address', 'address_queryset': address_queryset})

    def post(self, request):
        # 添加地址
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        # 校验
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})
        # 校验手机号
        if not re.match(r'^1[3-9][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机号格式错误'})

        # 添加地址
        try:
            address = Address.objects.get(user=request.user, is_default=True)
        except Address.DoesNotExist:
            # 不存在默认收货地址
            address = None
        if address:
            is_default = False
        else:
            is_default = True
        # 添加地址
        Address.objects.create(
            user=request.user,
            receiver=receiver,
            addr=addr,
            zip_code=zip_code,
            phone=phone,
            is_default=is_default,
        )

        return redirect(reverse('user:address'))






