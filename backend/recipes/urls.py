from django.urls import path

from recipes.views import load_url

urlpatterns = [
    path('s/<str:short_link>/', load_url, name='load-url'),
]
