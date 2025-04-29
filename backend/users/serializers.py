from django.contrib.auth import get_user_model
from djoser import serializers as DJserializers
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import Recipe
from users.fields import Base64ImageField
from users.models import Follow

User = get_user_model()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для сохранения аватара."""

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = (
            'avatar',
        )


class CreateUsrrSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя."""

    password = serializers.CharField(style={"input_type": "password"},
                                     write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserListSerializer(DJserializers.UserSerializer):
    """Сериализатор отображения пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'avatar',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        read_only_fields = ('email',)

    def get_is_subscribed(self, obj):
        current_user = self.context.get('request').user
        return (
            current_user.is_authenticated
            and obj.following.filter(user=current_user).exists()
        )


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
        request = self.context.get('request')
        if request.user == data['following']:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return UserSubscribesSerializer(
            instance.following,
            context={'request': request}
        ).data


class RecipeForSubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор реуептов для подписки."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSubscribesSerializer(UserListSerializer):
    """Сериализатор для предоставления информации
    о подписках пользователя.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserListSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit and not isinstance(recipes_limit, int):
            recipes = obj.recipes.all()[:int(recipes_limit)]
        return RecipeForSubscriptionsSerializer(
            recipes,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
