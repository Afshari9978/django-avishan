from typing import List, Union, Optional, Tuple

from colour import Color as ColorFromColour


class Color(ColorFromColour):

    def is_dark(self) -> bool:
        return self.get_brightness() < 128

    def get_brightness(self):
        rgb = self.get_rgb()
        r, g, b = int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
        return (r * 299 + g * 587 + b * 114) / 1000


class BootstrapClass:
    class_prefix = None

    def __init__(self, all: int = None, top: int = None, right: int = None, bottom: int = None, left: int = None):
        self.top = self.right = self.bottom = self.left = None

        if all:
            self.top = self.right = self.bottom = self.left = all
        if top is not None:
            self.top = top
        if right is not None:
            self.right = right
        if bottom is not None:
            self.bottom = bottom
        if left is not None:
            self.left = left

    def get_class(self):
        text = ""
        if self.bottom == self.left == self.right == self.top and self.bottom is not None:
            return f'{self.class_prefix}-{self.bottom}'

        if self.top is not None:
            text += f'{self.class_prefix}t-{self.top} '
        if self.right is not None:
            text += f'{self.class_prefix}r-{self.right} '
        if self.bottom is not None:
            text += f'{self.class_prefix}b-{self.bottom} '
        if self.left is not None:
            text += f'{self.class_prefix}l-{self.left} '
        return text

    def __str__(self):
        return self.get_class()


class Margin(BootstrapClass):
    class_prefix = 'm'


class Padding(BootstrapClass):
    class_prefix = 'p'


class DivComponent:
    def __init__(self,
                 element_kind: str = None,
                 added_classes: str = None,
                 margin: Margin = None,
                 padding: Padding = None
                 ):
        self.element_kind = element_kind
        self.margin = margin
        self.padding = padding
        self.items: List[DivComponent] = []
        self.added_classes = added_classes

    def add_item(self, item: 'DivComponent'):
        self.items.append(item)
        return self

    def add_items(self, items: List['DivComponent']):
        for item in items:
            self.add_item(item)
        return self


class Navbar:
    def __init__(self,
                 background_color: Color = Color('white'),
                 color: Color = None
                 ):
        self.background_color = background_color
        self.lightness_class = 'navbar-dark' if background_color.is_dark() else 'navbar-light'
        self.color = color if color is not None else (
            Color('white') if self.background_color.is_dark() else Color('black'))
        self.navbar_items: List[NavbarItem] = []

    def add_item(self, navbar_item: 'NavbarItem') -> 'Navbar':
        self.navbar_items.append(navbar_item)
        return self


class NavbarItem:
    def __init__(self,
                 link: str = "",
                 icon: str = "fa-ellipsis-h"
                 ):
        self.link = link
        self.icon = icon


class Badge:

    def __init__(self,
                 text: str,
                 span_class: str = 'badge-info'
                 ):
        self.text = text,
        self.span_class = span_class


class SidebarItem(NavbarItem):

    def __init__(self,
                 text: str,
                 link: str = "",
                 icon: str = "fa-ellipsis-h",
                 active: bool = False,
                 badge: Badge = None
                 ):
        super().__init__(link, icon)
        self.badge = badge
        self.active = active
        self.text = text
        self.element_type = 'sidebar_item'
        self.children: List[SidebarItem] = []

    @classmethod
    def create_from_view(cls, view_class):
        from avishan.views.panel_views import AvishanPanelWrapperView

        view_class: AvishanPanelWrapperView
        raise NotImplementedError

    def add_child(self, sidebar_item: 'SidebarItem') -> 'SidebarItem':
        self.children.append(sidebar_item)
        return self


class SidebarHeader:
    def __init__(self,
                 text: str
                 ):
        self.text = text
        self.element_type = 'sidebar_header'


class Sidebar:
    def __init__(self):
        self.sidebar_items: List[Union[SidebarItem, SidebarHeader]] = []

    def add_item(self, item: Union[SidebarItem, SidebarHeader]) -> 'Sidebar':
        self.sidebar_items.append(item)
        return self


class Row(DivComponent):

    def __init__(self, **kwargs):
        super().__init__(element_kind='row', **kwargs)


class Col(DivComponent):
    element_type = 'col'

    def __init__(self,
                 extra_small: int = None,
                 small: int = None,
                 medium: int = None,
                 large: int = None,
                 extra_large: int = None,
                 **kwargs
                 ):
        super().__init__(element_kind='col', **kwargs)
        self.extra_small = extra_small
        self.small = small
        self.medium = medium
        self.large = large
        self.extra_large = extra_large

    @property
    def added_classes(self):
        text = ""
        if self.extra_small:
            text += f'col-{self.extra_small} '
        if self.small:
            text += f'col-sm-{self.small} '
        if self.medium:
            text += f'col-md-{self.medium} '
        if self.large:
            text += f'col-lg-{self.large} '
        if self.extra_large:
            text += f'col-xl-{self.extra_large} '
        if len(text) == 0:
            return 'col'
        else:
            if self._added_classes:
                return text + self._added_classes  # todo check works fine
            else:
                return text[:-1]

    @added_classes.setter
    def added_classes(self, data):
        self._added_classes = data


class CardTab(DivComponent):
    def __init__(self, title: str, body: DivComponent, **kwargs):
        super().__init__(element_kind='card_tab', **kwargs)
        self.title = title
        self.body = body


class CardHeader(DivComponent):

    def __init__(self,
                 title: str = "",
                 buttons: List['Button'] = (),
                 **kwargs):
        super().__init__(element_kind='card-header', **kwargs)
        self.title = title
        self.buttons = buttons


class CardFooter(DivComponent):
    def __init__(self, **kwargs):
        super().__init__(element_kind='card-footer', **kwargs)


class Card(DivComponent):
    def __init__(self,
                 header: CardHeader = CardHeader(),
                 body: DivComponent = None,
                 footer: CardFooter = None,
                 body_added_classes: str = "",
                 **kwargs):
        super().__init__(element_kind='card', **kwargs)
        self.header = header
        self.body = body
        self.footer = footer
        self.body_added_classes = body_added_classes
        self.tabs: List[CardTab] = []

    def add_item(self, item: 'DivComponent'):
        if not self.body:
            self.body = DivComponent()
        self.body.items.append(item)
        return self

    def add_tab(self, tab: CardTab):
        self.tabs.append(tab)
        return self


class RawDivComponent(DivComponent):
    def __init__(self, raw: str, **kwargs):
        super().__init__(element_kind='raw', **kwargs)
        self.raw = raw


class Button(DivComponent):
    def __init__(self,
                 text: str,
                 type: str = 'button',
                 added_classes: str = 'btn-primary',
                 link: str = "",
                 **kwargs):
        super().__init__(element_kind='button', added_classes=added_classes, **kwargs)
        self.text = text
        self.type = type
        self.link = link


class PaginationItem:
    def __init__(self, text: str, disabled: bool = False, current: bool = False, url: str = None):
        self.url = url
        self.text = text
        self.disabled = disabled
        self.current = current


class Pagination(DivComponent):
    def __init__(self,
                 base_url: str,
                 total_pages: int,
                 current_page: int = 1,
                 **kwargs):
        super().__init__(element_kind='pagination', **kwargs)
        self.base_url = base_url
        self.total_pages = total_pages
        self.current_page = current_page

    def create_items(self) -> List[PaginationItem]:
        def add_page_to_url(base, page):
            pass

        # todo
        items = [
            PaginationItem(text='ابتدا', disabled=True, url='/panel'),
            PaginationItem(text='۱', url='/panel'),
            PaginationItem(text='۲', current=True, url='/panel'),
            PaginationItem(text='انتها', url='/panel'),
        ]

        return items


class FormElement(DivComponent):
    def __init__(self,
                 name: str,
                 type: str,
                 label: str,
                 disabled: bool = False,
                 **kwargs
                 ):
        super().__init__(element_kind='form-group', **kwargs)
        self.form: Optional[Form] = None
        self._name = name
        self.type = type
        self.label = label
        self._disabled = disabled
        self._margin = kwargs.get('margin')
        self._padding = kwargs.get('padding')

    @property
    def name(self):
        return self.form.name + "__" + self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def disabled(self):
        return self._disabled if self._disabled else self.form.disabled

    @disabled.setter
    def disabled(self, entered):
        self._disabled = entered

    @property
    def margin(self):
        return self._margin if self._margin else self.form.items_margin

    @margin.setter
    def margin(self, entered):
        self._margin = entered

    @property
    def padding(self):
        return self._padding if self._padding else self.form.items_padding

    @padding.setter
    def padding(self, entered):
        self._padding = entered


class InputFormElement(FormElement):
    def __init__(self,
                 input_type: str = 'text',
                 place_holder: str = "",
                 value: str = "",
                 **kwargs):
        super().__init__(type='input', **kwargs)
        self.input_type = input_type
        self.place_holder = place_holder
        self.value = value


class IconAddedInputFormElement(InputFormElement):
    def __init__(self,
                 input_type: str = 'text',
                 place_holder: str = "",
                 value: str = "",
                 fa_icon: str = 'fa-pencil',
                 **kwargs
                 ):
        kwargs['added_classes'] = kwargs.get('added_classes', ' ') + 'input-group'
        super().__init__(input_type, place_holder, value, **kwargs)
        self.fa_icon = fa_icon
        self.type = 'icon_added_input'


class FileChooseFormElement(FormElement):
    def __init__(self, **kwargs):
        super().__init__(type='file_input', **kwargs)


class Form(DivComponent):
    # todo https://www.w3schools.com/html/html_forms.asp
    def __init__(self,
                 action_url: str,
                 name: str,
                 method: str = 'post',
                 button: Button = Button(text='ثبت', type='submit', added_classes='btn-primary'),
                 items_margin: Margin = Margin(bottom=2),
                 items_padding: Padding = Padding(all=0),
                 disabled: bool = False,
                 encode: str = "",
                 **kwargs
                 ):
        super().__init__(element_kind='form', **kwargs)
        self.method = method
        self.name = name
        self.action_url = action_url
        self.encode = encode
        button.type = 'submit' if button.type != 'submit' else button.type
        button.added_classes = 'btn-primary btn-block' \
            if button.added_classes == 'btn-primary' \
            else button.added_classes
        self.button: Button = button
        self.items_margin = items_margin
        self.items_padding = items_padding
        self.disabled = disabled

    def add_item(self, form_item: FormElement):
        form_item.form = self
        if isinstance(form_item, FileChooseFormElement):
            self.encode = 'enctype="multipart/form-data"'
        return super().add_item(item=form_item)

    def add_items(self, form_items: List[FormElement]):
        for item in form_items:
            self.add_item(item)
        return self

    def set_button(self, button: Button):
        self.button = button
        return self

    def parse(self, data: dict):
        # todo check for added only names
        return data


class TableHead(DivComponent):
    def __init__(self,
                 name: str,
                 title: str,
                 converter_function=None,
                 **kwargs):
        super().__init__(element_kind='table_head', **kwargs)
        self.name = name
        self.title = title
        self.converter_function = converter_function


class TableItem(DivComponent):
    def __init__(self,
                 data_dict: dict = None,
                 **kwargs):
        super().__init__(element_kind='table_item', **kwargs)
        self.table: Optional[Table] = None
        if data_dict is None:
            data_dict = {}
        self.data_dict = data_dict

    def raw_data(self) -> List[str]:
        data = []
        for head in self.table.heads:
            if head.name not in self.data_dict.keys():
                data.append('UNKNOWN')
                continue
            if head.converter_function:
                data.append(head.converter_function(self.data_dict[head.name]))
            else:
                data.append(self.data_dict[head.name])
        return data

    def link(self):
        try:
            return f'{self.table.link_prepend}{self.data_dict[self.table.link_head_key]}{self.table.link_append}'
        except KeyError:
            return f'{self.table.link_prepend}UNKNOWN{self.table.link_append}'


class Table(DivComponent):
    def __init__(self,
                 heads: List[TableHead] = (),
                 link_head_key: str = None,
                 link_prepend: str = "",
                 link_append: str = "",
                 **kwargs):
        super().__init__(element_kind='table', **kwargs)
        self.heads = heads
        self.link_head_key = link_head_key
        self.link_prepend = link_prepend
        self.link_append = link_append

    def add_item(self, item: TableItem):
        item.table = self
        self.items.append(item)
        return self

    def add_items(self, items: List[TableItem]):
        for item in items:
            self.add_item(item)
        return self


class DataList(DivComponent):
    def __init__(self, **kwargs):
        super().__init__(element_kind='data_list', **kwargs)

    def add_item(self, item: Tuple[str, str]):
        self.items.append(item)
        return self

    def add_items(self, items: List[Tuple[str, str]]):
        for item in items:
            self.add_item(item)
        return self


class UnorderedList(DivComponent):
    def __init__(self, **kwargs):
        super().__init__(element_kind='unordered_list', **kwargs)

    def add_item(self, item: 'UnorderedListItem'):
        item: DivComponent
        return super().add_item(item)

    def add_items(self, items: List['UnorderedListItem']):
        items: List[DivComponent]
        return super().add_items(items)


class UnorderedListItem:
    def __init__(self, data: str, link: str = None):
        self.data = data
        self.link = link


class LineChartJs(DivComponent):
    class LineData:
        def __init__(self, title: str, color: str = "#007bff", data_list: list = None):
            if data_list is None:
                data_list = []
            self.color = color
            self.title = title
            self.data_list = data_list

    def __init__(self, name: str, labels: List[str] = None, settings: List[str] = (), **kwargs):
        super().__init__(element_kind='line_chart_js', **kwargs)
        if labels is None:
            labels = []
        self.labels = labels
        self.name = name
        self.settings = settings

    def add_item(self, item: Union[LineData, DivComponent]):
        return super().add_item(item)


class BarChartJs(DivComponent):
    class BarData:
        def __init__(self, title: str, color: str = "#007bff", data_list: list = None):
            if data_list is None:
                data_list = []
            self.color = color
            self.title = title
            self.data_list = data_list

    def __init__(self, name: str, labels: List[str] = None, **kwargs):
        super().__init__(element_kind='line_chart_js', **kwargs)
        if labels is None:
            labels = []
        self.labels = labels
        self.name = name

    def add_item(self, item: Union[BarData, DivComponent]):
        return super().add_item(item)


class TimelineItem:
    def __init__(self,
                 time: str = "",
                 title: str = "",
                 body_text: str = "",
                 buttons: List[Button] = (),
                 fa_icon: str = "fa-info"
                 ):
        self.time = time
        self.title = title
        self.body_text = body_text
        self.buttons = buttons
        self.fa_icon = fa_icon


class TimelineSection:
    def __init__(self, title: str, items: List[TimelineItem] = None):
        if items is None:
            items = []
        self.title = title
        self.items = items


class Timeline(DivComponent):
    def __init__(self, sections: List[TimelineSection] = (), **kwargs):
        super().__init__(element_kind='timeline', **kwargs)
        self.sections = sections


class DashboardItem:
    def __init__(self, item, row: int = 0, order: int = 0, col: Col = Col(6)):
        self.order = order
        self.item = item
        self.row = row
        self.col = col


class InfoBox(DivComponent):
    def __init__(self,
                 title: str,
                 value: str,
                 fa_icon: str,
                 **kwargs):
        super().__init__(element_kind='info_box', **kwargs)
        self.title = title
        self.value = value
        self.fa_icon = fa_icon
