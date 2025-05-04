from django.urls import include, path
from rest_framework import routers
from .views import (
    IngredientViewSet, RecipesViewSet, TagSlugViewSet,
    FollowViewSet, UserSubscribeView, UserViewSet, load_url
)

app_name = 'api'

router = routers.DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagSlugViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipesViewSet, basename='recipes')

urlpatterns = [
    path('users/subscriptions/', FollowViewSet.as_view({'get': 'list'})),
    path('users/<int:user_id>/subscribe/', UserSubscribeView.as_view()),
    path('s/<str:short_link>/', load_url, name='load_url'),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
