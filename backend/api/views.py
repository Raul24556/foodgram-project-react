from http import HTTPStatus
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, mixins
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, SAFE_METHODS, AllowAny, IsAuthenticated
)
from rest_framework.response import Response
from django.db.models import Exists, OuterRef
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_GET
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.views import APIView

from api.filters import RecipeFilter
from api.form_text import download
from api.pagination import RecipePagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    FavoritRecipesSerializer, IngredientSerializer, RecipeCreateSerializer,
    RecipesListSerializer, ShoppingCartSerializer, TagSlugSerializer,
    AvatarSerializer, FollowSerializer, UserSubscribesSerializer
)
from recipes.models import (
    FavoritRecipe, Ingredient, Recipe, ShoppingCart, TagSlug
)
from users.models import User, Follow
from foodgram.settings import SHORT_LINK_LENGTH


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
        queryset = Recipe.objects.all()
        # Добавляем аннотацию для всех пользователей
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    FavoritRecipe.objects.filter(
                        user=self.request.user, recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user, recipe=OuterRef('pk'))
                )
            )
        else:
            # Для неавторизованных пользователей
            # добавляем поля со значением False
            queryset = queryset.annotate(
                is_favorited=Exists(
                    FavoritRecipe.objects.none()
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.none()
                )
            )

        # Фильтрация по параметрам is_favorited и is_in_shopping_cart
        is_favorited = self.request.query_params.get('is_favorited', None)
        if is_favorited == '1':
            if self.request.user.is_authenticated:
                favorited_recipe_ids = FavoritRecipe.objects.filter(
                    user=self.request.user).values_list('recipe_id', flat=True)
                queryset = queryset.filter(id__in=favorited_recipe_ids)
            else:
                queryset = queryset.none()

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart', None)
        if is_in_shopping_cart == '1':
            if self.request.user.is_authenticated:
                cart_recipe_ids = ShoppingCart.objects.filter(
                    user=self.request.user).values_list('recipe_id', flat=True)
                queryset = queryset.filter(id__in=cart_recipe_ids)
            else:
                queryset = queryset.none()

        return queryset

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipesListSerializer
        return RecipeCreateSerializer

    def get_serializer_context(self):
        # Передаем контекст с запросом для сериализатора
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @action(["get"], detail=True, url_path='get-link')
    def get_link(self, request, pk):
        """Генерация короткой ссылки."""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = recipe.short_link
        if not short_link or len(short_link) != SHORT_LINK_LENGTH:
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


@require_GET
def load_url(request, short_link):
    """Перенаправление с короткой ссылки на страницу рецепта."""
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return HttpResponseRedirect(
        request.build_absolute_uri(reverse('recipes-detail',
                                           kwargs={'pk': recipe.id}))
    )
