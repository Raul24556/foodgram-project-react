import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        file_path = settings.BASE_DIR / 'data/ingredients.csv'
        ingredients = []
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(
                csvfile, fieldnames=('name', 'measurement_unit'))
            for row in tqdm(reader, desc="Importing ingredients"):
                ingredients.append(Ingredient(**row))
        Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(
            'Успешно импортированные ингредиенты'))
