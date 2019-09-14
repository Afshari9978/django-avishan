import datetime

from ..exceptions import ValidatorException
from ..utils.data_functions import convert_to_en_number, convert_to_fa_number, introduce_code_length, has_numbers

# todo in minimum length ha max nadarn?


def validate_phone_number(input: str, country_code: str = '98', phone_start_number: str = '09') -> str:
    input = convert_to_en_number(input)
    input = input.replace(" ", "")
    input = input.replace("-", "")

    if input.startswith("00"):
        if not input.startswith("00" + country_code):
            raise ValidatorException('شماره موبایل')
        if input.startswith("00" + country_code + phone_start_number):
            input = "00" + country_code + input[5:]
    elif input.startswith("+"):
        if not input.startswith("+" + country_code):
            raise ValidatorException('شماره موبایل')
        input = "00" + input[1:]
        if input.startswith("00" + country_code + phone_start_number):
            input = "00" + country_code + input[5:]
    elif input.startswith(phone_start_number):
        input = "00" + country_code + input[1:]

    if len(input) != 14 or not input.isdigit():
        raise ValidatorException('شماره موبایل')

    return input


def validate_text(input: str, blank: bool = True) -> str:
    input = input.strip()
    input = convert_to_fa_number(input)

    if not blank and len(input) == 0:
        raise ValidatorException('متن')

    return input


def validate_recommend_code(input: str) -> str:
    input = validate_text(input)

    input = convert_to_en_number(input)

    input = input.upper()

    return input


def validate_first_name(input):
    input = input.strip()

    if has_numbers(input) or len(input) < 2:
        raise ValidatorException('نام')

    return input


def validate_last_name(input):
    input = input.strip()

    if has_numbers(input) or len(input) < 2:
        raise ValidatorException('نام خانوادگی')

    return input


def validate_ferdowsi_student_id(input):
    input = validate_text(input, blank=False)

    if not input.isdigit():
        raise ValidatorException('شماره دانشجویی')
    return input


def validate_plate(plate_a, plate_b, plate_c, plate_d):
    plate_a = validate_text(convert_to_fa_number(plate_a), blank=False)
    plate_b = validate_text(convert_to_fa_number(plate_b), blank=False)
    plate_c = validate_text(convert_to_fa_number(plate_c), blank=False)
    plate_d = validate_text(convert_to_fa_number(plate_d), blank=False)

    if plate_b not in ['ب', 'ج', 'د', 'س', 'ص', 'ط', 'ق', 'ل', 'م', 'ن', 'و', 'ه', 'ی', 'الف', 'پ', 'ت', 'ث', 'ز', 'ژ',
                       'ش', 'ع', 'ف', 'ک', 'گ', 'D', 'S', 'd', 's', 'ي']:
        raise ValidatorException('پلاک')

    if not plate_a.isdigit() or not plate_c.isdigit() or not plate_d.isdigit():
        raise ValidatorException('پلاک')

    return plate_a, plate_b, plate_c, plate_d


def validate_time(input: dict, name: str) -> datetime.time:
    return datetime.time(int(input['hour']), int(input['minute']))
