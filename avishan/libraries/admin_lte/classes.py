from typing import List


class DataListItem:
    def __init__(self, item_id_field: str, **kwargs):
        self.item_id_field = item_id_field
        for key, value in kwargs.items():
            self.__setattr__(key, value)

    def get_id(self):
        return self.__getattribute__(self.item_id_field)


class DataList:
    def __init__(self, headers: List[str] = (), items: List[DataListItem] = ()):
        self.headers = headers
        self.items = items

    def raw(self) -> List[dict]:
        data = []
        for item in self.items:
            part = {
                'data': [],
                'id': item.get_id()
            }
            for header in self.headers:
                part['data'].append(item.__dict__.get(header))
            data.append(part)
        return data
