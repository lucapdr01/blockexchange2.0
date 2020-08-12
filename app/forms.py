from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Wallet, OrderPlacer


class RegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = ["username", "password1", "password2", ]


class UserProfileForm(forms.ModelForm):

    class Meta:
        model = Wallet
        fields = ('startBtc',)
        widgets = {'startBtc': forms.HiddenInput()}


class OrderForm(forms.ModelForm):
    class Meta:
        model = OrderPlacer
        fields = ('btcs', 'price')
