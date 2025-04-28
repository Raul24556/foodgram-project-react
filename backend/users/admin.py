from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from recipes.models import (FavoritRecipe, Ingredient, IngredientsRecipe,
                            Recipe, ShoppingCart, ShortUrlModel, TagSlug)
from users.models import Follow, User


class IngredientInline(admin.TabularInline):
    model = IngredientsRecipe
    extra = 0


class UserAdmin(BaseUserAdmin):
    list_display = ('username',
                    'email',
                    'count_follows',
                    'count_recipes'
                    )
    search_fields = ('username',
                     'email',
                     )

    @admin.display(description="Количество подписчиков")
    def count_follows(self, obj):
        return obj.follower.all().count()

    @admin.display(description="Количество рецептов")
    def count_recipes(self, obj):
        return obj.recipes.all().count()


class RecipeAdmin(admin.ModelAdmin):
    search_fields = ('name',
                     'author__username',)
    list_display = ('name',
                    'author',
                    'count_in_favorit',
                    )
    list_filter = ('tags',
                   )
    inlines = (
        IngredientInline,
    )

    @admin.display(description="Количество в избранном")
    def count_in_favorit(self, obj):
        return obj.favotit_recipes.all().count()


class IngredientAdmin(admin.ModelAdmin):
    search_fields = ('name',
                     )
    list_display = ('name',
                    'measurement_unit',
                    )


admin.site.register(TagSlug)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShortUrlModel)
admin.site.register(IngredientsRecipe)
admin.site.register(ShoppingCart)
admin.site.register(FavoritRecipe)


admin.site.register(User, UserAdmin)
admin.site.register(Follow)
