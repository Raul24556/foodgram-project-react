from django_filters import ModelMultipleChoiceFilter, NumberFilter
from django_filters.rest_framework import FilterSet

from recipes.models import Recipe, TagSlug


class RecipeFilter(FilterSet):
    """Фильтр по полю автор и тег."""

    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=TagSlug.objects.all(),
        conjoined=False
    )
    is_in_shopping_cart = NumberFilter(
        method='filter_is_in_shopping_cart')
    is_favorited = NumberFilter(
        method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favotit_recipes__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_carts__user=self.request.user)
        return queryset
