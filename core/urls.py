"""
URLs temporales para la app core.
"""
from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

app_name = 'core'

@login_required
def home_view(request):
    """Vista temporal para la página home."""
    context = {
        'title': 'Bienvenido al Sistema Escolar',
        'user': request.user,
    }
    return render(request, 'core/home.html', context)

urlpatterns = [
    path('', home_view, name='home'),
]
