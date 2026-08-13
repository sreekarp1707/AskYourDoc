from django import forms
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required = True)
    password1 = forms.CharField(
        label = 'Enter Password',
        widget = forms.PasswordInput()
    )
    password2 = forms.CharField(
        label = 'Re-Enter Password',
        widget = forms.PasswordInput()
    )
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget = forms.TextInput(
            attrs = {
                "class" : "form-control",
                "placeholder" : "Enter Your Username"
            }
        )
    )        
    password = forms.CharField(
        widget = forms.PasswordInput(
            attrs = {
                "class" : "form-control",
                "placeholder" : "Enter Your Password"
            }
        )
    )