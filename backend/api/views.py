import logging
from http import HTTPStatus

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import RecipeFilter
from api.form_text import download
from api.pagination import RecipePagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer, FavoritRecipesSerializer, FollowSerializer,
    IngredientSerializer, RecipeCreateSerializer, RecipesListSerializer,
    ShoppingCartSerializer, TagSlugSerializer, UserSubscribesSerializer
)
from recipes.models import (FavoritRecipe,
                            Ingredient, Recipe,
                            ShoppingCart, TagSlug)
from users.models import Follow, User

logger = logging.getLogger(__name__)


class TagSlugViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin, viewsets.GenericViewSet):
    """Вьюсет для тегов."""
    queryset = TagSlug.objects.all()
    serializer_class = TagSlugSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin, viewsets.GenericViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ('name',)
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""
    serializer_class = RecipesListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = RecipePagination
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return Recipe.objects.annotate_for_user(self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return RecipesListSerializer
        return RecipeCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @action(["get"], detail=True, url_path='get-link')
    def get_link(self, request, pk):
        """Генерация короткой ссылки."""
        from django.conf import settings
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = recipe.short_link
        if not short_link or len(short_link) != settings.SHORT_LINK_LENGTH:
            return Response(
                {'errors': 'Короткая ссылка отсутствует или некорректна'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        base_url = request.build_absolute_uri('/').rstrip('/')
        return Response({"short-link": f"{base_url}/s/{short_link}"},
                        status=HTTPStatus.OK)

    @action(["post", "delete"], detail=True)
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.add_to_model(request, FavoritRecipesSerializer, recipe)
        return self.delete_from_model(request, FavoritRecipe, recipe)

    @action(["post", "delete"], detail=True)
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.add_to_model(request, ShoppingCartSerializer, recipe)
        return self.delete_from_model(request, ShoppingCart, recipe)

    @action(["get"], detail=False)
    def download_shopping_cart(self, request):
        ingredients = 'recipe__ingredient_recipes__ingredients'
        ingredients_amount = 'recipe__ingredient_recipes__amount'
        shopping_cart = ShoppingCart.objects.filter(
            user=request.user).values(ingredients_amount, ingredients)
        return download(shopping_cart, ingredients, ingredients_amount)

    def add_to_model(self, request, serializer_class, recipe):
        serializer = serializer_class(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from_model(self, request, model, recipe):
        deleted, _ = model.objects.filter(
            user=request.user, recipe=recipe).delete()
        if not deleted:
            return Response(
                {'errors': 'Нет такого рецепта в избранном' if model
                    == FavoritRecipe else 'Нет такого рецепта в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(DjoserUserViewSet):
    """Вьюсет пользователей."""
    permission_classes = [AllowAny]

    @action(["get"], detail=False, permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(["put", "delete"], detail=False,
            url_path='me/avatar', url_name='me-avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request):
        instance = request.user
        if request.method == "DELETE":
            instance.avatar.delete()
            instance.avatar = None
            instance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class FollowViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Вьюсет подписчиков."""
    permission_classes = [AllowAny]
    serializer_class = UserSubscribesSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class UserSubscribeView(APIView):
    """Создание или удаление подписки на пользователя."""

    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        serializer = FollowSerializer(
            data={'user': request.user.id, 'following': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        deleted, _ = Follow.objects.filter(
            user=request.user, following=author).delete()
        if not deleted:
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
