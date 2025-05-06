import random
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Exists, OuterRef

from recipes.constants import (
    AMOUNT_INGREDIENT, COOKING_TIME_MIN, INGREDIENT_MASUREMENT_UNIT,
    INGREDIENT_NAME, RECIPE_NAME_MAX_LENGTH, TAG_SLUG_NAME_MAX_LENGTH
)

User = get_user_model()


class RecipeManager(models.Manager):
    def annotate_for_user(self, user):
        queryset = self.get_queryset()
        if user.is_authenticated:
            return queryset.annotate(
                is_favorited=Exists(
                    FavoritRecipe.objects.filter(
                        user=user, recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk'))
                )
            )
        return queryset.annotate(
            is_favorited=Exists(FavoritRecipe.objects.none()),
            is_in_shopping_cart=Exists(ShoppingCart.objects.none())
        )


class TagSlug(models.Model):
    name = models.CharField(
        unique=True,
        max_length=TAG_SLUG_NAME_MAX_LENGTH,
        verbose_name='Тег',
    )
    slug = models.SlugField(
        unique=True,
        max_length=TAG_SLUG_NAME_MAX_LENGTH,
        verbose_name='Слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ("name",)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=INGREDIENT_NAME,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_MASUREMENT_UNIT,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredients'
            )
        ]

    def __str__(self):
        return f'{self.name} Единица измерения {self.measurement_unit}'


class Recipe(models.Model):
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientsRecipe',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        TagSlug,
        verbose_name='Теги'
    )
    image = models.ImageField(
        upload_to='recipes_img/images/',
        verbose_name='Картинка, закодированная в Base64',
    )
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(
            COOKING_TIME_MIN,
            'Минимальное время приготовления'
        )],
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True
    )
    short_link = models.CharField(
        max_length=settings.SHORT_LINK_LENGTH,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Короткая ссылка'
    )

    objects = RecipeManager()

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ("-pub_date",)

    def __str__(self):
        return self.name

    def generate_short_link(self):
        characters = string.ascii_letters + string.digits
        while True:
            short_link = ''.join(random.choice(characters)
                                 for _ in range(settings.SHORT_LINK_LENGTH))
            if not Recipe.objects.filter(short_link=short_link).exists():
                return short_link

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)


class IngredientsRecipe(models.Model):
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиенты'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(
            AMOUNT_INGREDIENT,
            'Минимальное количество ингредиента'
        )],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        default_related_name = 'ingredient_recipes'
        ordering = ("recipe",)
        constraints = [
            models.UniqueConstraint(
                fields=('ingredients', 'recipe'),
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return (
            f'Ингредиент {self.ingredients} в {self.recipe} '
            f'в количестве {self.amount}'
        )


class UserRecipeBase(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_%(class)s'
            )
        ]


class ShoppingCart(UserRecipeBase):
    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_carts'
        ordering = ("user",)

    def __str__(self):
        return f'Рецепт {self.recipe} в корзине у пользователя {self.user}'


class FavoritRecipe(UserRecipeBase):
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        default_related_name = 'favorite_recipes'
        ordering = ("user",)

    def __str__(self):
        return f'Рецепт {self.recipe} в избранном у пользователя {self.user}'
