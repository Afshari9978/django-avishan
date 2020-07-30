from typing import List, Tuple

import requests

from avishan.configure import get_avishan_config


def distance_matrix(origins: List[Tuple[float, float]], destinations: List[Tuple[float, float]]) -> \
        List[List[Tuple[float, float]]]:
    if len(origins) == 0 or len(destinations) == 0:
        raise ValueError('length of entered lists can\'t be 0')
    origins_text = ''
    for item in origins:
        origins_text += f'|{item[0]},{item[1]}'
    destinations_text = ''
    for item in destinations:
        destinations_text += f'|{item[0]},{item[1]}'

    url = f'https://api.neshan.org/v1/distance-matrix?' \
          f'origins={origins_text[1:]}&destinations={destinations_text[1:]}'
    response = requests.get(
        url=url,
        headers={'Api-Key': get_avishan_config().NESHAN_API_KEY}
    ).json()

    data = []
    for row in response['rows']:
        data.append([(element['distance']['value'], element['duration']['value']) for element in row['elements']])
    return data
