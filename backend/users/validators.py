from django.core.exceptions import ValidationError

from core.constants import DONT_USE_IN_USERNAME


def check_me_in_username(value):
    if value == DONT_USE_IN_USERNAME:
        raise ValidationError(
            message='Для имени пользователя '
            f'нельзя использовать {DONT_USE_IN_USERNAME}.',
        )
    return value
