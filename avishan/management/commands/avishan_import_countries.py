import requests

from avishan.models import Country
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Imports countries from https://restcountries.eu/rest/v2/all'

    def handle(self, *args, **kwargs):

        response = requests.get(url='https://restcountries.eu/rest/v2/all').json()

        for item in response:
            if item['numericCode'] is None:
                print(f'{item["name"]} skipped')
                continue
            try:
                country = Country.objects.get(numeric_code=item['numericCode'])
                country.update(
                    name=item['name'],
                    alpha_2_code=item['alpha2Code'],
                    alpha_3_code=item['alpha3Code'],
                    region=item['region'],
                    native_name=item['nativeName'],
                    flag=item['flag']
                )
                print(f'update {country.name}')
            except Country.DoesNotExist:
                country = Country.create(
                    numeric_code=item['numericCode'],
                    name=item['name'],
                    alpha_2_code=item['alpha2Code'],
                    alpha_3_code=item['alpha3Code'],
                    region=item['region'],
                    native_name=item['nativeName'],
                    flag=item['flag']
                )
                print(f'create {country.name}')
