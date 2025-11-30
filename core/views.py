from django.views.generic import TemplateView


class HomeView(TemplateView):
    """
    Vista de inicio del sistema.
    """
    template_name = 'home.html'
