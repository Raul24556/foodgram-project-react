from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.db import models
from django.db.models import F, Q

from users.constants import EMAIL_LENGTH, USER_NAME_LENGTH


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "password"]

    first_name = models.CharField('Имя', max_length=USER_NAME_LENGTH)
    last_name = models.CharField('Фамилия', max_length=USER_NAME_LENGTH)
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=EMAIL_LENGTH,
        unique=True,
        validators=(EmailValidator,)
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
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user', 'following')
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique_following'
            ),
            models.CheckConstraint(
                check=~Q(user=F('following')),
                name='prevent_self_follow'
            )
        )

    def __str__(self):
        return f'{self.user} подписан на {self.following}'
