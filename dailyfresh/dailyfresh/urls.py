# coding: utf-8
"""dailyfresh URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url,include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^tinymce/', include('tinymce.urls')), # 富文本编辑器
    url(r'^search', include('haystack.urls')), # 全文检索框架
    url(r'^user/',include('user.urls', namespace='user')), # 用户模块
    url(r'^order/',include('order.urls', namespace='order')), # 订单模块
    url(r'^cart/',include('cart.urls', namespace='cart')), # 购物车模块
    url(r'^',include('goods.urls', namespace='goods')), # 商品模块 放在最后因为是从上向下开始匹配
]
