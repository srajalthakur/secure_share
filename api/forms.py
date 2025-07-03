from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import UploadedFile, User

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class FileUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'})
        }

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'is_ops', 'is_client', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_ops': forms.CheckboxInput(),
            'is_client': forms.CheckboxInput(),
        }
