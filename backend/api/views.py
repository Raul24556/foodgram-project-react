from http import HTTPStatus

from rest_framework import mixins
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        SAFE_METHODS, AllowAny)
from rest_framework.response import Response

from api import filters  # Исправлено: используем filters правильно
from api.form_text import download
from api.pagination import RecipePagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (FavoritRecipesSerializer,
                             IngredientSerializer, RecipeCreateSerializer,
                             RecipesListSerializer, ShoppingCartSerializer,
                             ShortUrlSerializer, TagSlugSerializer)

from recipes.models import (FavoritRecipe, Ingredient, Recipe,
                            ShoppingCart, ShortUrlModel,
                            TagSlug)


class TagSlugViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """Вьюсет для тегов."""

    queryset = TagSlug.objects.all()
    serializer_class = TagSlugSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ('name',)
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipesListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.RecipeFilter
    pagination_class = RecipePagination
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipesListSerializer
        return RecipeCreateSerializer

    @action(["get"], detail=True, url_path='get-link')
    def get_link(self, request, pk):
        """Функция генерации и записи коротких ссылок."""
        original_url = request.build_absolute_uri(
            reverse('api:recipes-detail', kwargs={'pk': pk})
        )
        generated_short_link = ShortUrlModel.generate_short_link()
        short_link = '/'.join((
            original_url.split('/api')[0], 's',
            generated_short_link
        ))
        original_url = ''.join(original_url.split('/api'))
        data = {
            'url': original_url,
            'short_link': generated_short_link,
        }
        serializer = ShortUrlSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"short-link": short_link}, status=HTTPStatus.OK)

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
            user=request.user
        ).values(ingredients_amount, ingredients)
        return download(shopping_cart, ingredients, ingredients_amount)

    def add_to_model(self, request, serializer_class, recipe):
        """Вспомогательная функция добавления в БД."""
        serializer = serializer_class(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete_from_model(self, request, model, recipe):
        """Вспомогательная функция удаления из БД."""
        if not model.objects.filter(
            user=request.user.id,
            recipe=recipe.id
        ).exists():
            return Response(
                {'errors': 'Нет такого рецепта в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.get(
            user=request.user.id,
            recipe=recipe.id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@require_GET
def load_url(request, short_link):
    """Перенаправление с короткой ссылки на обычную."""
    original_url = get_object_or_404(
        ShortUrlModel, short_link=short_link
    ).url
    return redirect(original_url)
