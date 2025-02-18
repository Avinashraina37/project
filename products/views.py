from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Product, Offer, Order, Categorie
from django.contrib.auth.models import User
from django.contrib import messages

# Create your views here.

def index(request):
    cart = request.session.get('cart')

    if not cart:
        request.session['cart'] = {}
    
    categories = Categorie.objects.all()
    categorie_id = request.GET.get('categorie')

    if categorie_id:
        if categorie_id == "10":
            products = Product.objects.all()
        else:
            products = Product.get_all_products_by_categorieid(categorie_id)
    else:
        products = Product.objects.all()

    data = {
        'products': products,
        'categories': categories
    }

    product = request.POST.get('product')
    remove = request.POST.get('remove')
    if product is not None:
        cart = request.session.get('cart')
        if cart:
            quantity = cart.get(product)
            if quantity:
                if remove:
                    if quantity <= 1:
                        cart.pop(product)
                    else:
                        cart[product] = quantity - 1
                else:
                    cart[product] = quantity + 1
            else:
                cart[product] = 1
        else:
            cart = {}
            cart[product] = 1

        request.session['cart'] = cart

    return render(request, 'index.html', data)

def cart(request):
    codes = ''
    if request.method == 'POST':
        codes = request.POST.get('getcode')
    
    offers = Offer.objects.all()
    ids = list(request.session.get('cart').keys())
    products = Product.get_products_by_id(ids)
    
    return render(request, 'cart.html', {'products': products, 'offers': offers, 'codes': codes})

def thank_you(request):
    if request.method == 'POST':
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        user_id = request.session.get('user_id')
        carts = request.session.get('cart')
        products = Product.get_products_by_id(list(carts.keys()))

        if not user_id:
            messages.error(request, "User not logged in")
            return redirect('/products/cart')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "Invalid user")
            return redirect('/products/cart')

        if len(phone) == 10 and phone[0] in "7896":
            for product in products:
                quantity = carts.get(str(product.id))
                
                # Check stock availability
                if product.stock >= quantity:
                    order = Order(
                        user=user,
                        product=product,
                        price=product.price,
                        quantity=quantity,
                        address=address,
                        phone=phone
                    )
                    order.place_order()

                    # Reduce the stock
                    product.stock -= quantity
                    product.save()
                else:
                    messages.error(request, f"Not enough stock for {product.name}")
                    return redirect('/products/cart')

            request.session['cart'] = {}
            return render(request, 'Thank you.html')
        else:
            messages.error(request, 'Invalid Phone number')
            return redirect('/products/cart')

    return redirect('/')
