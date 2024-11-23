from django import forms
from.models import User

class RegisterForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['username','email','password']
        
   #Todo form validation if need
   
class LoginForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['email','password']
        
    #Todo from validation if need
   