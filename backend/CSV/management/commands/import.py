# python manage.py import ingredients.csv

import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from recipes.models import Ingredient

PATH_TO_FILE_FOR_IMPORT = 'data/'


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str, help=u'Название файла')

    def handle(self, *args, **kwargs):
        file_name = kwargs['file_name']

        with open(
            (settings.BASE_DIR / PATH_TO_FILE_FOR_IMPORT / file_name),
            'r', newline='', encoding='utf-8'
        ) as csvfile:
            spamreader = csv.DictReader(
                csvfile, fieldnames=('name', 'measurement_unit')
            )
            for row in tqdm(spamreader, ncols=80):
                try:
                    Ingredient.objects.create(**row)
                except ValueError as er:
                    tqdm.write(f'Ошибка {er}')
