import csv

from django.http import HttpResponse

from recipes.models import Ingredient


def download(shopping_cart, ingredients, ingredients_amount):
    """Подготовка и скачивание списка."""
    cart = {}
    for ingredient_set in shopping_cart:
        if ingredient_set[ingredients] not in cart:
            cart[
                ingredient_set[ingredients]
            ] = ingredient_set[ingredients_amount]
        cart[
            ingredient_set[ingredients]
        ] = cart[
            ingredient_set[ingredients]
        ] + ingredient_set[ingredients_amount]
    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="some.csv"'
        },
    )
    writer = csv.writer(response)
    for ing, amount in cart.items():
        ingredient = Ingredient.objects.get(pk=ing)
        writer.writerow([ingredient, amount, ingredient.measurement_unit])
    return response
