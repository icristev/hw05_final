from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


def authorized_only(func):
    def check_users(request, *arg, **kwargs):
        if request.user.is_authenticated:
            return func(request, *arg, **kwargs)
        return redirect('/auth/login/')
    return check_users
