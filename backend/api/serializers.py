from rest_framework import serializers

from core.constants import AMOUNT_INGREDIENT, COOKING_TIME_MIN
from recipes.models import (FavoritRecipe, Ingredient, IngredientsRecipe,
                            Recipe, ShoppingCart, ShortUrlModel, TagSlug)
from users.serializers import Base64ImageField, UserListSerializer


class TagSlugSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = TagSlug
        fields = (
            'id',
            'name',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = IngredientsRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipesListSerializer(serializers.ModelSerializer):
    """Сериализатор списка рецептов."""

    tags = TagSlugSerializer(many=True, read_only=True)
    author = UserListSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        read_only=True,
        source='ingredient_recipes',
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        current_user = self.context.get('request').user
        return (
            current_user.is_authenticated
            and obj.favotit_recipes.filter(user=current_user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        current_user = self.context.get('request').user
        return (
            current_user.is_authenticated
            and obj.shopping_carts.filter(user=current_user).exists()
        )


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    """Вспомогательный сериализатор ингредиентов для создания рецепто."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientsRecipe
        fields = (
            'id',
            'amount'
        )

    def validate(self, data):
        if data.get('amount') < AMOUNT_INGREDIENT:
            raise serializers.ValidationError(
                'Количество ингредиентов '
                f'не может быть меньше {AMOUNT_INGREDIENT}'
            )
        return data


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериалайзер создания Рецептов"""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=TagSlug.objects.all(),
        many=True
    )
    ingredients = IngredientInRecipeCreateSerializer(
        many=True,
        source='ingredient_recipes',
    )
    image = Base64ImageField()
    author = UserListSerializer(read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            "author",
        )

    def validate_cooking_time(self, value):
        """Валидация времени готовки."""

        if value < COOKING_TIME_MIN:
            raise serializers.ValidationError(
                f"Время готовки не может быть меньше {COOKING_TIME_MIN}"
            )
        return value

    def validate_tags(self, tags):
        """Валидатор тегов."""

        if not tags:
            raise serializers.ValidationError(
                "Рецепт не может быть без Тегов"
            )
        elif len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                "Нельзя добавить одинаковые теги"
            )
        return tags

    def validate(self, data):
        """Валидатор отсутствия нужных полей."""

        if ('ingredient_recipes' not in data or not data.get(
            'ingredient_recipes'
        )):
            raise serializers.ValidationError(
                "Не добавлены ингредиенты"
            )
        elif 'tags' not in data:
            raise serializers.ValidationError(
                "Не добавлены теги"
            )
        elif len(data.get('ingredient_recipes')) != len(set(
            [ing_id['id'] for ing_id in data.get('ingredient_recipes')]
        )):
            raise serializers.ValidationError(
                "Нельзя добавить одинаковые ингредиенты"
            )
        return data

    def add_ingredients(self, ingredients, recipe):
        """Вспомогательная функция для добавления ингредиентов.
        Используется при создании/редактировании рецепта."""
        ingredient_list = [
            IngredientsRecipe(
                recipe=recipe,
                ingredients=ingredient.get('id'),
                amount=ingredient.get('amount')
            ) for ingredient in ingredients
        ]
        IngredientsRecipe.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        request = self.context.get('request')
        ingredients = validated_data.pop('ingredient_recipes')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        self.add_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredient_recipes')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        IngredientsRecipe.objects.filter(recipe=instance).delete()
        self.add_ingredients(ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipesListSerializer(
            instance,
            context={'request': request}
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Короткое представление рецепта."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'image',
            'name',
            'cooking_time',
        )


class ShortUrlSerializer(serializers.Serializer):
    """Сериализатор коротких ссылок."""

    short_link = serializers.CharField()
    url = serializers.URLField(required=True)

    def create(self, validated_data):
        return ShortUrlModel.objects.create(**validated_data)

    def to_representation(self, instance):
        return {'short-link': instance.short_link}


class FavoritRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор модели избанного."""

    class Meta:
        model = FavoritRecipe
        fields = (
            'user',
            'recipe',
        )

    def validate_recipe(self, recipe):
        current_user = self.context.get('request').user
        if FavoritRecipe.objects.filter(
            user=current_user,
            recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                "Уже в избранном"
            )
        return recipe

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': request}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор модели корзины покупок."""

    class Meta:
        model = ShoppingCart
        fields = (
            'user',
            'recipe',
        )

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': request}
        ).data

    def validate_recipe(self, recipe):
        current_user = self.context.get('request').user
        if ShoppingCart.objects.filter(
            user=current_user,
            recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                "Уже в корзине"
            )
        return recipe
