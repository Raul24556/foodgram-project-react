from django.contrib import admin

from recipes.models import (
    FavoritRecipe,
    Ingredient,
    IngredientsRecipe,
    Recipe,
    ShoppingCart,
    TagSlug
)


class IngredientInline(admin.TabularInline):
    model = IngredientsRecipe
    extra = 0
    min_num = 1


@admin.register(TagSlug)
class TagSlugAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
    )
    search_fields = (
        'name',
        'slug',
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = (
        'name',
    )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'count_in_favorit',
    )
    search_fields = (
        'name',
        'author__username',
    )
    list_filter = (
        'tags',
    )
    inlines = (
        IngredientInline,
    )

    @admin.display(description="Количество в избранном")
    def count_in_favorit(self, obj):
        return obj.favorite_recipes.all().count()


@admin.register(IngredientsRecipe)
class IngredientsRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'recipe',
        'ingredients',
        'amount',
    )
    search_fields = (
        'recipe__name',
        'ingredients__name',
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = (
        'user__username',
        'recipe__name',
    )


@admin.register(FavoritRecipe)
class FavoritRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = (
        'user__username',
        'recipe__name',
    )
