from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_GET

from recipes.models import Recipe


@require_GET
def load_url(request, short_link):
    """Перенаправление с короткой ссылки на страницу рецепта."""
    try:
        recipe = Recipe.objects.get(short_link=short_link)
        return HttpResponseRedirect(
            request.build_absolute_uri(reverse(
                'recipes-detail', kwargs={'pk': recipe.id}))
        )
    except Recipe.DoesNotExist:
        return HttpResponseRedirect('/404')
