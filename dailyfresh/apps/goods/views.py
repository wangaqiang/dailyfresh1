from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.core.cache import cache
from django.core.paginator import Paginator
from goods.models import GoodsType, IndexGoodsBanner, GoodsSKU, IndexPromotionBanner, IndexTypeGoodsBanner
from order.models import OrderGoods
from django_redis import get_redis_connection

# Create your views here.
class IndexView(View):
    '''首页'''
    def get(self, request):
        '''显示首页'''
        # 尝试从缓存中获取数据
        context = cache.get('index_page_data')
        if context is None:
            print("——————————————————————————————测试专属——————————————————————————————————")
            # 缓存中没有数据
            # 获取商品的种类信息
            types = GoodsType.objects.all()
    
            # 获取首页轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')
    
            # 获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
    
            # 获取首页分类商品展示信息
            for type1 in types: # GoodsType
                # 获取type种类首页分类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type1, display_type=1).order_by('index')
                # 获取type种类首页分类商品的文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type1, display_type=0).order_by('index')
    
                # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
                type1.image_banners = image_banners
                type1.title_banners = title_banners
    
            context = {'types':types,
                    'goods_banners':goods_banners,
                    'promotion_banners':promotion_banners}
                
            # 设置缓存
            cache.set('index_page_data', context, 3600) # key value timeout

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已经登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context.update(cart_count=cart_count)

        # 使用模板
        return render(request, 'index.html', context)

# /goods/商品id
class DetailView(View):
    '''详情页'''
    def get(self, request, goods_id):
        '''显示详情页'''
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return redirect(reverse('goods:index'))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取商品的评论信息
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取同一个SPU的其他规格商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)


        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已经登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            cart_count = conn.hlen(cart_key)
            
        # 组织模板上下文
        context = {'sku':sku,
                   'types':types,
                   'sku_orders':sku_orders,
                   'new_skus':new_skus,
                   'same_spu_skus':same_spu_skus,
                   'cart_count':cart_count}

        # 使用模板
        return render(request, 'detail.html', context)


# 种类id 页码 排序方式
# /List?type_id=种类id&page=页码&sort=排序方式
# /List/种类id/页码/排序方式
# /List/种类id/页码？sort=排序方式
class ListView(View):
    '''列表页'''
    def get(self, request, type_id, page):
        '''显示列表页'''
        # 获取种类信息
        try:
            type1 = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 种类不存在
            return redirect(reverse('goods:index'))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取排序的方式 获取分类商品的信息
        # sort=default 按照默认id排序
        # sort=price 按照商品价格排序
        # sort=hot 按照商品销量排序
        sort = request.GET.get('sort')
        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type1).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type1).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type1).order_by('-id')

        # 对数据进行分页
        paginator = Paginator(skus, 1)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page对象
        skus_page = paginator.page(page)

        # 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页的话，显示1～5页
        # 3.如果当前是后3页，显示后5页
        # 其他情况，显示当前页的前两页，当前页，当前页的后两页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1,num_pages+1)
        elif page <= 3:
            pages = range(1,6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4,num_pages+1)
        else:
            pages = range(page-2, page+3)

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=type1).order_by('-create_time')[:2]
        
        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已经登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context = {'type':type1,
                   'types':types,
                   'skus_page':skus_page,
                   'new_skus':new_skus,
                   'cart_count':cart_count,
                   'pages':pages,
                   'sort':sort}

        # 使用模板
        return render(request, 'list.html', context)