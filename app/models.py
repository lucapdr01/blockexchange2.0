from django.db import models
import json
from bson import ObjectId
from djongo.models.fields import ObjectIdField
from django.contrib.auth.models import User


class SellOrder:
    _id = ObjectId()
    fillPrice = 0

    def __init__(self, btcs, price, filled):
        self.btcs = btcs
        self.price = price
        self.filled = filled

    @property
    def id(self):
        return self._id


class BuyOrder:
    _id = ObjectId()
    fillPrice = 0

    def __init__(self, btcs, price, filled):
        self.btcs = btcs
        self.price = price
        self.filled = filled

    @property
    def id(self):
        return self._id

# Data container
class Wallet(models.Model):

    _id = ObjectIdField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    startBtc = models.FloatField(default=0)
    btcBalance = models.FloatField(default=0)
    profit = models.FloatField(default=0)
    buyOrders = models.Field(default='', blank=True)
    sellOrders = models.Field(default='', blank=True)

    def Buy(self, btcs, price):
        order = BuyOrder(btcs, price, False)
        jsonOrder = json.dumps({
            "id": str(order.id),
            "btcs": order.btcs,
            "price": order.price,
            "fillprice": order.fillPrice,
            "filled": order.filled
        })
        self.buyOrders += jsonOrder
        self.save()
        self.buyOrders += ";"
        self.save()

    def Sell(self, btcs, price):
        order = SellOrder(btcs, price, False)
        jsonOrder = json.dumps({
            "id":str(order.id),
            "btcs": order.btcs,
            "price": order.price,
            "fillprice": order.fillPrice,
            "filled": order.filled
        })
        self.sellOrders += jsonOrder
        self.save()
        self.sellOrders += ";"
        self.save()

    def UpdateBtc(self):
        plusBtc = 0
        minusBtc = 0

        buyArr = self.buyOrders.split(';')
        sellArr = self.sellOrders.split(';')
        buyArr.pop()
        sellArr.pop()

        for item in buyArr:
            jsonItem = json.loads(item)
            if jsonItem['filled']:
                plusBtc += float(jsonItem['btcs'])

        for item in sellArr:
            jsonItem = json.loads(item)
            minusBtc += float(jsonItem['btcs'])

        self.btcBalance = self.startBtc - minusBtc + plusBtc
        self.save()

    def CalcProfit(self):
        buyArr = self.buyOrders.split(';')
        sellArr = self.sellOrders.split(';')
        buyArr.pop()
        sellArr.pop()
        self.profit = 0

        for item in buyArr:
            jsonItem = json.loads(item)
            if jsonItem['filled']:
                profit = (int(jsonItem['fillprice']) - int(jsonItem['price'])) * float(jsonItem['btcs'])
                self.profit += profit
                self.save()

        for item in sellArr:
            jsonItem = json.loads(item)
            if jsonItem['filled']:
                profit = (int(jsonItem['fillprice']) - int(jsonItem['price'])) * int(jsonItem['btcs'])
                self.profit += profit
                self.save()

    def JsonBuyList(self):
        buyList = []
        if self.buyOrders is not None:
            buyArr = self.buyOrders.split(';')
            buyArr.pop()
            for item in buyArr:
                jsonItem = json.loads(item)
                if not jsonItem['filled']:
                    buyList += [jsonItem]
        return buyList

    def JsonSellList(self):
        sellList = []
        if self.sellOrders is not None:
            sellArr = self.sellOrders.split(';')
            sellArr.pop()
            for item in sellArr:
                jsonItem = json.loads(item)
                if not jsonItem['filled']:
                    sellList += [jsonItem]
        return sellList


class OrderPlacer(models.Model):
    _id = ObjectIdField()
    btcs = models.IntegerField()
    price = models.IntegerField()






