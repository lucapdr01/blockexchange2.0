from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm, UserProfileForm, OrderForm
from django.contrib.auth.models import User
from random import randrange
from json2html import *
import json


def home(request):
    users = User.objects.all()
    return render(request, "app/home.html", {'users': users})


def filled(request):
    return render(request, "app/filled.html", {})


def orders(request):
    results = orderBook()

    # arrays all containing buy and sell orders
    buys = results[0]
    buys = buys[::-1]
    sells = results[1]
    sells = sells[::-1]

    htmlBuys = json2html.convert(json=buys, table_attributes=" class=\"table table-striped\"")
    htmlSells = json2html.convert(json=sells, table_attributes=" class=\"table table-striped\"")

    return render(request, "app/orders.html", {"buys": htmlBuys, "sells": htmlSells})


def userPage(request):
    if request.user.is_authenticated and not request.user.is_superuser:
        # Get data from database to render order book
        results = orderBook()

        # arrays all containing buy and sell orders
        buys = results[0]
        buys = buys[::-1]
        sells = results[1]
        sells = sells[::-1]

        htmlBuys = json2html.convert(json=buys, table_attributes=" class=\"table table-striped\"")
        htmlSells = json2html.convert(json=sells, table_attributes=" class=\"table table-striped\"")

        myBuys = request.user.wallet.JsonBuyList()
        mySells = request.user.wallet.JsonSellList()

        myHtmlBuys = json2html.convert(json=myBuys, table_attributes=" class=\"table table-striped\"")
        myHtmlSells = json2html.convert(json=mySells, table_attributes=" class=\"table table-striped\"")

        # User Btc balance
        request.user.wallet.UpdateBtc()
        btc = request.user.wallet.btcBalance
        # User profit balance
        request.user.wallet.CalcProfit()
        profit = request.user.wallet.profit

        if request.method == "POST":

            form = OrderForm(request.POST)
            # sell operation
            if 'sell' in request.POST:
                # check if the user has enough BTCs to sell
                if float(btc) >= float(form.data['btcs']):
                    request.user.wallet.Sell(form.data['btcs'], form.data['price'])
                else:
                    newForm = OrderForm()
                    users = User.objects.all()
                    return render(request, "app/userpage.html", {"form": newForm, "btc": btc, "profit": profit,
                                                                 "users": users, "buys": htmlBuys, "sells": htmlSells,
                                                                 "mybuys": myHtmlBuys, "mysells": myHtmlSells})
            # buy operation
            elif 'buy' in request.POST:
                print('buy')
                request.user.wallet.Buy(form.data['btcs'], form.data['price'])

            if form.is_valid():
                form.save()

                res = orderBook()
                buys = res[0]
                sells = res[1]

                # function that checks if the sell order placed is ready to be filled with another buy
                if 'sell' in request.POST:
                    sellOrder(request, sells, buys)
                    return redirect("/filled")

                # function that checks if the buy order placed is ready to be filled with another sell
                elif 'buy' in request.POST:
                    buyOrder(request, sells, buys)
                    return redirect("/filled")

                return redirect("/filled")
        else:
            # initialise blank form
            form = OrderForm()

        users = User.objects.all()
        return render(request, "app/userpage.html", {"form": form, "btc": btc, "profit": profit, "users": users,
                                                     "buys": htmlBuys, "sells": htmlSells, "mybuys": myHtmlBuys,
                                                     "mysells": myHtmlSells})
    else:
        return render(request, "app/userpage.html", {})


def orderBook():
    users = User.objects.all()
    buyList = []
    sellList = []
    for user in users:
        if hasattr(user, 'wallet'):
            buyList += user.wallet.JsonBuyList()
            sellList += user.wallet.JsonSellList()

    orderedBuy = sorted(buyList, key=lambda x: x['price'])
    orderedSell = sorted(sellList, key=lambda x: x['price'])

    return orderedBuy, orderedSell


def buyOrder(request, sell_list, buy_list):

    for sell in sell_list:
        # check if buy price is grater
        if buy_list and sell['price'] <= buy_list[-1]['price']:
            print('Order Filled')
            buyArr = request.user.wallet.JsonBuyList()

            # full-fill both orders
            if float(sell['btcs']) == float(buy_list[-1]['btcs']):
                # mark both orders as filled

                buyArr[-1]['filled'] = True
                buyArr[-1]['fillprice'] = sell['price']
                request.user.wallet.buyOrders = ""
                request.user.wallet.save()

                for buy in buyArr:
                    request.user.wallet.buyOrders += json.dumps(buy)
                    request.user.wallet.buyOrders += ";"
                request.user.wallet.save()

                # Update Values
                request.user.wallet.UpdateBtc()
                request.user.wallet.CalcProfit()

                users = User.objects.all()
                for user in users:
                    if hasattr(user, 'wallet'):
                        sellArr = user.wallet.JsonSellList()
                        if user.wallet.sellOrders and sell in sellArr:

                            # Mark sell as filled
                            user.wallet.sellOrders = ""
                            user.wallet.save()

                            for sellItem in sellArr:
                                if sellItem == sell:
                                    sellItem['filled'] = True
                                    sellItem['fillprice'] = buy_list[-1]['price']
                                user.wallet.sellOrders += json.dumps(sellItem)
                                user.wallet.sellOrders += ";"
                            user.wallet.save()

                            # Update values
                            user.wallet.UpdateBtc()
                            user.wallet.CalcProfit()

                            return

            # full-fill buy and partially-fill sell
            elif float(sell['btcs']) > float(buy_list[-1]['btcs']):

                difference = float(sell['btcs']) - float(buy_list[-1]['btcs'])

                # Buy filled
                buyArr[-1]['filled'] = True
                buyArr[-1]['fillprice'] = sell['price']
                request.user.wallet.buyOrders = ""
                request.user.wallet.save()

                for buy in buyArr:
                    request.user.wallet.buyOrders += json.dumps(buy)
                    request.user.wallet.buyOrders += ";"
                request.user.wallet.save()

                # Update values
                request.user.wallet.UpdateBtc()
                request.user.wallet.CalcProfit()

                users = User.objects.all()

                for user in users:
                    if hasattr(user, 'wallet'):
                        sellArr = user.wallet.JsonSellList()
                        if user.wallet.sellOrders and sell in sellArr:

                            # Mark sell as filled
                            user.wallet.sellOrders = ""
                            user.wallet.save()

                            for sellItem in sellArr:
                                if sellItem == sell:

                                    sellItem['btcs'] = float(sellItem['btcs']) - difference
                                    sellItem['filled'] = True
                                    sellItem['fillprice'] = buy_list[-1]['price']

                                    user.wallet.Sell(difference, sellItem['price'])

                                user.wallet.sellOrders += json.dumps(sellItem)
                                user.wallet.sellOrders += ";"
                            user.wallet.save()

                            # Update values
                            user.wallet.UpdateBtc()
                            user.wallet.CalcProfit()

                            return
            # full-fill sell and partially-fill buy
            elif float(sell['btcs']) < float(buy_list[-1]['btcs']):

                difference = float(buy_list[-1]['btcs']) - float(sell['btcs'])

                # Buy filles
                buyArr[-1]['btcs'] = float(buyArr[-1]['btcs']) - difference
                buyArr[-1]['filled'] = True
                buyArr[-1]['fillprice'] = sell['price']

                request.user.wallet.buyOrders = ""
                request.user.wallet.save()

                for buy in buyArr:
                    request.user.wallet.buyOrders += json.dumps(buy)
                    request.user.wallet.buyOrders += ";"
                request.user.wallet.save()

                request.user.wallet.Buy(difference, buyArr[-1]['price'])

                # Update values
                request.user.wallet.UpdateBtc()
                request.user.wallet.CalcProfit()

                users = User.objects.all()

                for user in users:
                    if hasattr(user, 'wallet'):
                        sellArr = user.wallet.JsonSellList()
                        if user.wallet.sellOrders and sell in sellArr:

                            user.wallet.sellOrders = ""
                            user.wallet.save()

                            for sellItem in sellArr:
                                if sellItem == sell:
                                    sellItem['filled'] = True
                                    sellItem['fillprice'] = buy_list[-1]['price']
                                user.wallet.sellOrders += json.dumps(sellItem)
                                user.wallet.sellOrders += ";"
                            user.wallet.save()

                            # Update values
                            user.wallet.UpdateBtc()
                            user.wallet.CalcProfit()

                            return


def sellOrder(request, sell_list, buy_list):
    for buy in buy_list[::-1]:
        # Check if buy price is grater
        if sell_list and buy['price'] >= sell_list[0]['price']:
            print('Order Filled')
            sellArr = request.user.wallet.JsonSellList()

            # full-fill both orders
            if float(buy['btcs']) == float(sell_list[0]['btcs']):
                # mark both orders as filled

                sellArr[-1]['filled'] = True
                sellArr[-1]['fillprice'] = buy['price']
                request.user.wallet.sellOrders = ""
                request.user.wallet.save()

                for sell in sellArr:
                    request.user.wallet.sellOrders += json.dumps(sell)
                    request.user.wallet.sellOrders += ";"
                request.user.wallet.save()

                # Update Values
                request.user.wallet.UpdateBtc()
                request.user.wallet.CalcProfit()

                users = User.objects.all()
                for user in users:
                    if hasattr(user, 'wallet'):
                        buyArr = user.wallet.JsonBuyList()
                        if user.wallet.buyOrders and buy in buyArr:

                            # Mark buy as filled
                            user.wallet.buyOrders = ""
                            user.wallet.save()

                            for buyItem in buyArr:
                                if buyItem == buy:
                                    buyItem['filled'] = True
                                    buyItem['fillprice'] = sell_list[0]['price']
                                user.wallet.buyOrders += json.dumps(buyItem)
                                user.wallet.buyOrders += ";"
                            user.wallet.save()

                            # Update values
                            user.wallet.UpdateBtc()
                            user.wallet.CalcProfit()

                            return

            # full-fill sell and partially-fill buy
            elif float(buy['btcs']) > float(sell_list[0]['btcs']):

                difference = float(buy['btcs']) - float(sell_list[0]['btcs'])

                # Sell filled
                sellArr[-1]['filled'] = True
                sellArr[-1]['fillprice'] = buy['price']
                request.user.wallet.sellOrders = ""
                request.user.wallet.save()

                for sell in sellArr:
                    request.user.wallet.sellOrders += json.dumps(sell)
                    request.user.wallet.sellOrders += ";"
                request.user.wallet.save()

                # Update values
                request.user.wallet.UpdateBtc()
                request.user.wallet.CalcProfit()

                users = User.objects.all()
                for user in users:
                    if hasattr(user, 'wallet'):
                        buyArr = user.wallet.JsonBuyList()
                        if user.wallet.buyOrders and buy in buyArr:

                            # Mark buy as filled
                            user.wallet.buyOrders = ""
                            user.wallet.save()

                            for buyItem in buyArr:
                                if buyItem == buy:

                                    buyItem['btcs'] = float(buyItem['btcs']) - difference
                                    buyItem['filled'] = True
                                    buyItem['fillprice'] = sell_list[-1]['price']

                                    user.wallet.Buy(difference,buyItem['price'])

                                user.wallet.buyOrders += json.dumps(buyItem)
                                user.wallet.buyOrders += ";"
                            user.wallet.save()

                            # Update values
                            user.wallet.UpdateBtc()
                            user.wallet.CalcProfit()

                            return
            # Full-fill buy and partially-fill sell
            elif float(buy['btcs']) < float(sell_list[0]['btcs']):

                difference = float(sell_list[0]['btcs']) - float(buy['btcs'])

                # Sell filled
                sellArr[-1]['btcs'] = float(sellArr[0]['btcs']) - difference
                sellArr[-1]['filled'] = True
                sellArr[-1]['fillprice'] = buy['price']

                request.user.wallet.sellOrders = ""
                request.user.wallet.save()

                for sell in sellArr:
                    request.user.wallet.sellOrders += json.dumps(sell)
                    request.user.wallet.sellOrders += ";"
                request.user.wallet.save()

                request.user.wallet.Sell(difference, sellArr[0]['price'])

                # Update values
                request.user.wallet.UpdateBtc()
                request.user.wallet.CalcProfit()

                users = User.objects.all()
                for user in users:
                    if hasattr(user, 'wallet'):
                        buyArr = user.wallet.JsonBuyList()
                        if user.wallet.buyOrders and buy in buyArr:

                            user.wallet.buyOrders = ""
                            user.wallet.save()

                            for buyItem in buyArr:
                                if buyItem == buy:
                                    buyItem['filled'] = True
                                    buyItem['fillprice'] = sell_list[0]['price']
                                user.wallet.buyOrders += json.dumps(buyItem)
                                user.wallet.buyOrders += ";"
                            user.wallet.save()

                            # Update values
                            user.wallet.UpdateBtc()
                            user.wallet.CalcProfit()

                            return


def register(request):
    if request.method == "POST":

        form = RegisterForm(request.POST)
        # Hidden form
        profileForm = UserProfileForm(request.POST)

        if form.is_valid() and profileForm.is_valid():

            user = form.save()
            profile = profileForm.save(commit=False)

            profile.user = user

            profile.save()

            return redirect("/")
    else:
        # Initialise blank form
        form = RegisterForm()
        profileForm = UserProfileForm(initial={'startBtc': randrange(10) + 1})

    # Render the page
    return render(request, "app/register.html", {"form": form, "profileform": profileForm})


# Handle logout
def logoutReq(request):
    logout(request)
    return redirect("/")


# Handle login
def loginReq(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:

                login(request, user)

                return redirect('/')
            else:
                return render(request, "app/login.html", {"form": form})
        else:
            return render(request, "app/login.html", {"form": form})

    form = AuthenticationForm()
    return render(request, "app/login.html", {"form": form})
