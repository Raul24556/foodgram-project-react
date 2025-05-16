from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.fields import Base64ImageField
from recipes.models import (FavoritRecipe, Ingredient,
                            IngredientsRecipe, Recipe,
                            ShoppingCart, TagSlug)
from users.models import Follow, User


class TagSlugSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = TagSlug
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit')

    class Meta:
        model = IngredientsRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class UserListSerializer(serializers.ModelSerializer):
    """Сериализатор отображения пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'avatar',
                  'first_name', 'last_name', 'is_subscribed')
        read_only_fields = ('email',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.following.filter(user=request.user).exists())


class RecipesListSerializer(serializers.ModelSerializer):
    """Сериализатор списка рецептов."""

    tags = TagSlugSerializer(many=True, read_only=True)
    author = UserListSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True, read_only=True, source='ingredient_recipes')
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    """Вспомогательный сериализатор ингредиентов для создания рецепта."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientsRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=TagSlug.objects.all(), many=True)
    ingredients = IngredientInRecipeCreateSerializer(
        many=True, source='ingredient_recipes')
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError("Рецепт не может быть без тегов")
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                "Нельзя добавить одинаковые теги")
        return tags

    def validate(self, data):
        required_fields = ['ingredient_recipes', 'tags',
                           'name', 'text', 'cooking_time', 'image']
        errors = {}
        for field in required_fields:
            if field not in data or data[field] is None or (
                    field == 'ingredient_recipes' and not data[field]):
                errors[field] = f"Поле '{field}' обязательно."
        if errors:
            raise serializers.ValidationError(errors)
        if 'ingredient_recipes' in data and len(
                data.get('ingredient_recipes')) != len(set(
                    [ing_id['id'] for ing_id in data.get('ingredient_recipes')]
                )):
            raise serializers.ValidationError(
                "Нельзя добавить одинаковые ингредиенты")
        return data

    def add_ingredients(self, ingredients, recipe):
        ingredient_list = [
            IngredientsRecipe(
                recipe=recipe,
                ingredients=ingredient.get('id'),
                amount=ingredient.get('amount')
            ) for ingredient in ingredients
        ]
        IngredientsRecipe.objects.bulk_create(ingredient_list)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredient_recipes')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data)
        recipe.tags.set(tags)
        self.add_ingredients(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredient_recipes')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        IngredientsRecipe.objects.filter(recipe=instance).delete()
        self.add_ingredients(ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipesListSerializer(instance, context=self.context).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Короткое представление рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'image', 'name', 'cooking_time')


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для сохранения аватара."""

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        if not data.get('avatar'):
            raise serializers.ValidationError(
                "Поле 'avatar' не может быть пустым или null.")
        return data


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор подписчиков."""

    class Meta:
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'following'],
                message='Вы уже подписаны'
            )
        ]
        model = Follow
        fields = ('user', 'following')

    def validate(self, data):
        following = data.get('following')
        if not User.objects.filter(id=following.id).exists():
            raise serializers.ValidationError(
                'Пользователь, на которого вы '
                'пытаетесь подписаться, не существует.'
            )
        if self.context['request'].user == following:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!')
        return data

    def to_representation(self, instance):
        return UserSubscribesSerializer(
            instance.following, context=self.context).data


class RecipeForSubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов для подписки."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSubscribesSerializer(UserListSerializer):
    """Сериализатор для предоставления информации о подписках пользователя."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserListSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get(
            'recipes_limit') if request else None
        recipes = obj.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        return RecipeForSubscriptionsSerializer(
            recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FavoritRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор модели избранного."""

    class Meta:
        model = FavoritRecipe
        fields = ('user', 'recipe')

    def validate_recipe(self, recipe):
        current_user = self.context.get('request').user
        if FavoritRecipe.objects.filter(
                user=current_user, recipe=recipe).exists():
            raise serializers.ValidationError("Уже в избранном")
        return recipe

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeMinifiedSerializer(
            instance.recipe, context={'request': request}).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор модели корзины покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeMinifiedSerializer(
            instance.recipe, context={'request': request}).data

    def validate_recipe(self, recipe):
        current_user = self.context.get('request').user
        if ShoppingCart.objects.filter(
                user=current_user, recipe=recipe).exists():
            raise serializers.ValidationError("Уже в корзине")
        return recipe
