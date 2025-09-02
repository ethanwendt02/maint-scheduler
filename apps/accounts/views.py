from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()           # creates inactive/basic user
            login(request, user)         # optionally auto-login after signup
            return redirect("login")     # or redirect to a dashboard
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
