from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
User = get_user_model()

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username") or None
        password = request.POST.get("password") or None
        if all([username, password]):
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                print("Logged in successfully!")
                return redirect("/")
            else:
                print("Invalid credentials!Try again.")
    return render(request, "auth/login.html", {})

def register_view(request):
    if request.method == "POST":

        username = request.POST.get("username") or None
        email = request.POST.get("email") or None
        password = request.POST.get("password") or None

        username_exists = User.objects.filter(username__iexact=username).exists()
        email_exists = User.objects.filter(email__iexact=email).exists()

        if not username_exists and not email_exists and all([username, email, password]):
            user = User.objects.create_user(username, email, password)
            print("User created successfully!")
            return redirect("/login")
        else:
            print("Username or email already taken.")
    return render(request, "auth/register.html", {})