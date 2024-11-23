from django.shortcuts import render,redirect
from .forms import RegisterForm,LoginForm
from .models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
# Create your views here.
def chat_view(request):
      return render(request,'chatapp/index.html')

def register_view(request):
      
      if request.method=="POST":
            regform=RegisterForm(request.POST)
            if regform.is_valid():
                  # Form data is already validated, so we can create the user
                  username=regform.cleaned_data['username']
                  email=regform.cleaned_data['email']
                  password=regform.cleaned_data['password']
                  # Create the user using the form data
                  user=User.objects.create_user(username=username,email=email,password=password)
                  user.save()
                  regform=RegisterForm()
                  messages.success(request,"registered successsfully")
                  return redirect('login')
            else:
                  messages.error(request,"Not valided data")
       
      regform=RegisterForm()        
                        
      return render(request,'chatapp/register.html',{'regform':regform})
      
def login_view(request):
      if request.method == 'POST':
           logform=LoginForm(request.POST)
           if logform.is_valid():
                 email=logform.cleaned_data['email']
                 password = logform.cleaned_data['password']
                 user=User.objects.get(email=email)
                 user=authenticate(request,username=user.username,enmail=email,password=password)
                 if user is not None:
                       login(request,user)
                       messages.success(request,"login successfully")
                       return redirect('chatview')
                 else:
                       messages.error(request,"invalid ceredentils")
           else:
            messages.error(request,"Not valided data")     
       
      else:
            logform=LoginForm()
                  
            
      return render(request,'chatapp/login.html',{'logform':logform})
            