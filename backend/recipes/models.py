import random
import string

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator
from django.db import models

from core.constants import (AMOUNT_INGREDIENT, COOKING_TIME_MIN,
                            INGREDIENT_MASUREMENT_UNIT, INGREDIENT_NAME,
                            RECIPE_NAME_MAX_LENGTH, SHORT_LINK_ID_LENGTH,
                            SHORT_LINK_URL_FIELD, TAG_SLUG_NAME_MAX_LENGTH)

User = get_user_model()


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
        verbose_name='Название ингридиента',
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_MASUREMENT_UNIT,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ("name", )
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

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ("-pub_date",)

    def __str__(self):
        return self.name


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
            'Минимальное время приготовления'
        )],
    )

    class Meta:
        verbose_name = 'Ингредиентов в рецепе'
        verbose_name_plural = 'Ингредиентов в рецепе'
        default_related_name = 'ingredient_recipes'
        ordering = ("recipe",)
        constraints = [
            models.UniqueConstraint(
                fields=('ingredients', 'recipe'),
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return (f'Ингредиент {self.ingredients} в {self.recipe}в'
                f' количистве {self.amount}')


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_carts'
        ordering = ("user",)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_cartshop'
            ),
        )

    def __str__(self):
        return (f'Рецепт {self.recipe}'
                f' в корзине у пользователя {self.user}')


class FavoritRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избанное'
        verbose_name_plural = 'Избранные'
        default_related_name = 'favotit_recipes'
        ordering = ("user",)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipes'
            ),
        )

    def __str__(self):
        return (f'Рецепт {self.recipe}'
                f' в избранном у пользователя {self.user}')


class ShortUrlModel(models.Model):
    short_link = models.CharField(
        max_length=SHORT_LINK_URL_FIELD,
        unique=True,
        verbose_name='Коротка ссылка',
    )
    url = models.URLField(
        verbose_name='Полная ссылка',)

    @classmethod
    def generate_short_link(cls):
        CHARACTERS = (
            string.ascii_uppercase
            + string.ascii_lowercase
            + string.digits
        )
        while True:
            short_link = ''.join(
                random.choice(CHARACTERS)
                for _ in range(SHORT_LINK_ID_LENGTH)
            )
            try:
                cls.objects.get(short_link=short_link)
            except ObjectDoesNotExist:
                return short_link

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
        ordering = ("url", )
        constraints = (
            models.UniqueConstraint(
                fields=('short_link', 'url'),
                name='unique_urls'
            ),
        )

    def __str__(self):
        return (f'Короткая ссылка: {self.short_link}'
                f' для ссылки {self.url}')
