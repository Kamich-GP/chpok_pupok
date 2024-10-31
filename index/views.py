from django.shortcuts import render, redirect
from .models import Product, Category, Cart
from .forms import SearchForm, RegForm
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
import telebot

bot = telebot.TeleBot('7606530458:AAEg7uCOGM7vQ-ebK-0i3XlNSD2gy3R5hBI')


# Create your views here.
def home_page(request):
    # Достаем данные из БД
    products = Product.objects.all()
    categories = Category.objects.all()
    # Достаем форму
    form = SearchForm
    # Отправляем данные на фронт
    context = {'products': products,
               'categories': categories,
               'form': form}

    return render(request, 'home.html', context)


def product_page(request, pk):
    # Достаем данные из БД
    product = Product.objects.get(id=pk)
    # Отправляем данные на фронт
    context = {'product': product}
    return render(request, 'product.html', context)


def category_page(request, pk):
    # Определяем выбранную категорию
    category = Category.objects.get(id=pk)
    exact_products = Product.objects.filter(product_category=category)
    # Отправляем данные на фронт
    context = {'category': category, 'products': exact_products}
    return render(request, 'category.html', context)


def search(request):
    if request.method == 'POST':
        get_product = request.POST.get('search_bar')

        if Product.objects.get(product_name__iregex=get_product):
            exact_product = Product.objects.get(product_name__iregex=get_product)
            return redirect(f'/product/{exact_product.id}')
        else:
            print('Не нашел')
            return redirect('/')


class Register(View):
    template_name = 'registration/register.html'

    def get(self, request):
        context = {'form': RegForm}
        return render(request, self.template_name, context)

    def post(self, request):
        form = RegForm(request.POST)

        # Если данные корректны
        if form.is_valid():
            username = form.clean_username()
            password2 = form.cleaned_data.get('password2')
            email = form.cleaned_data.get('email')

            user = User.objects.create_user(username=username,
                                            email=email,
                                            password=password2)
            user.save()
            login(request, user)
            return redirect('/')
        # Если данные некорректны
        context = {'form': RegForm}
        return render(request, self.template_name, context)


def logout_view(request):
    logout(request)
    return redirect('/')


def to_cart(request, pk):
    if request.method == 'POST':
        product = Product.objects.get(id=pk)
        if product.product_count >= int(request.POST.get('pr_amount')):
            Cart.objects.create(user_id=request.user.id,
                                user_product=product,
                                user_product_quantity=int(request.POST.get('pr_amount'))).save()
            return redirect('/')


def del_from_cart(request, pk):
    product_to_del = Product.objects.get(id=pk)
    Cart.objects.filter(user_product=product_to_del, user_id=request.user.id).delete()

    return redirect('/cart')


def cart_page(request):
    user_cart = Cart.objects.filter(user_id=request.user.id)
    product_ids = [i.user_product.id for i in user_cart]
    user_pr_amounts = [a.user_product_quantity for a in user_cart]
    product_counts = [c.user_product.product_count for c in user_cart]
    totals = [round(t.user_product_quantity * t.user_product.product_price, 2) for t in user_cart]
    text = (f'Новый заказ!\n'
            f'Клиент: {User.objects.get(id=request.user.id).email}\n\n')

    if request.method == 'POST':
        for i in range(len(product_ids)):
            product = Product.objects.get(id=product_ids[i])
            product.product_count = product_counts[i] - user_pr_amounts[i]
            product.save(update_fields=['product_count'])

        for i in user_cart:
            text += (f'Товар: {i.user_product}\n'
                     f'Количество: {i.user_product_quantity}\n')

        text += f'\nИтог: {round(sum(totals))}'
        bot.send_message(6775701667, text)
        user_cart.delete()
        return redirect('/')

    context = {'cart': user_cart, 'totals': totals, 'summary': round(sum(totals), 2), 'total': 0}
    return render(request, 'cart.html', context)



