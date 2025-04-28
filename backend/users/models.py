from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator, RegexValidator
from django.db import models

from core.constants import EMAIL_LENGTH, USER_NAME_LENGTH
from users.validators import check_me_in_username


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "password"]

    first_name = models.CharField(
        'Имя',
        max_length=USER_NAME_LENGTH
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=USER_NAME_LENGTH
    )
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=EMAIL_LENGTH,
        unique=True,
        validators=(EmailValidator,)
    )
    username = models.CharField(
        'username',
        max_length=USER_NAME_LENGTH,
        unique=True, validators=[
            RegexValidator(
                regex=r'^[a-zA-Z][a-zA-Z0-9-_\.]{1,20}$',
                message='Неверное имя пользователя',
                code='invalid_username'
            ),
            check_me_in_username
        ]
    )
    avatar = models.ImageField(
        upload_to='avatar/images/',
        verbose_name='Картинка, закодированная в Base64',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return f'{self.username} {self.email}'


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='follower'
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        verbose_name = 'Подписки'
        verbose_name_plural = 'Подписки'
        ordering = ('user',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique_following'
            ),
        )

    def __str__(self):
        return (f'{self.user}'
                f' подписан на {self.following}')
