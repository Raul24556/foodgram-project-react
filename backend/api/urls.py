from django.urls import include, path
from rest_framework import routers

from api.views import IngredientViewSet, RecipesViewSet, TagSlugViewSet
from users.views import FollowViewSet, UserSubscribeView, UserViewSet

app_name = 'api'

router = routers.DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagSlugViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipesViewSet, basename='recipes')

urlpatterns = [
    path(r'users/subscriptions/', FollowViewSet.as_view({'get': 'list'})),
    path(r'users/<int:user_id>/subscribe/', UserSubscribeView.as_view()),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
