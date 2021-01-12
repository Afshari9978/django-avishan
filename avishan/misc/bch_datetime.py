from khayyam import JalaliDate, JalaliDatetime
from datetime import timedelta, datetime, date, time
from typing import Union, List

# todo: type hints
from avishan.misc.translation import AvishanTranslatable


class BchDatetime(object):
    def __init__(self, year: Union[int, datetime, date, JalaliDatetime, dict, 'BchDatetime'] = None, month: int = None,
                 day: int = None,
                 hour: int = None, minute: int = None,
                 second: int = None, microsecond: int = None) -> None:
        temp = None

        # todo not safe
        if not year and not month and not day and not hour and not minute and not second and not microsecond:
            temp = BchDatetime.from_bch_datetime(BchDatetime.now())
        elif isinstance(year, datetime):
            temp = BchDatetime.from_datetime(year)
        elif isinstance(year, date):
            temp = BchDatetime.from_date(year)
        elif isinstance(year, JalaliDatetime):
            temp = BchDatetime.from_jalali_datetime(year)
        elif isinstance(year, dict):
            temp = BchDatetime.from_dict(year)
        elif isinstance(year, BchDatetime):
            temp = year

        if temp:
            self.year, self.month, self.day, self.hour, self.minute, self.second, self.microsecond = \
                temp.year, temp.month, temp.day, temp.hour, temp.minute, temp.second, temp.microsecond
            return
        self.year = year
        if isinstance(month, str):
            try:
                month = int(month)
            except ValueError:
                try:
                    month = {
                        'فروردین': 1,
                        'اردیبهشت': 2,
                        'خرداد': 3,
                        'تیر': 4,
                        'مرداد': 5,
                        'شهریور': 6,
                        'مهر': 7,
                        'آبان': 8,
                        'آذر': 9,
                        'دی': 10,
                        'بهمن': 11,
                        'اسفند': 12,
                    }[month]
                except KeyError:
                    from avishan.exceptions import ErrorMessageException
                    raise ErrorMessageException(AvishanTranslatable(
                        EN=f'Unknown Month String {month}',
                        FA=f'عبارت ناشناخته ماه {month}'
                    ))
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.microsecond = microsecond

        """
        YYYY: year in 4 digit (1397) 
        YY00: last year in 2 digit (97)
        cYYY: year in complete digit (14)

        MM00: month in 2 digit (02)
        cM00: month in complete digit (2)

        DD00: day in 2 digit (09)
        cD00: day in complete digit (1)

        hh00: hour in 2 digit (04)
        ch00: hour in complete digit (3)
        mm00: minute in 2 digit (59)
        cm00: minute in complete digit (2)       

        ss00: second in 2 digit (59)
        cs00: second in complete digit (2)

        00ii: microseconds in 3 digit (999)
        0ii0: microseconds in 6 digit (999999)
        ci00: microseconds in real digit (17)
        """

    @property
    def year(self):
        return self.__year

    @year.setter
    def year(self, year):
        if year:
            self.__year = int(year)
        else:
            self.__year = 1

    @property
    def month(self):
        return self.__month

    @month.setter
    def month(self, month):
        if month:
            self.__month = int(month)
        else:
            self.__month = 1

    @property
    def day(self):
        return self.__day

    @day.setter
    def day(self, day):
        if day:
            self.__day = int(day)
        else:
            self.__day = 1

    @property
    def hour(self):
        return self.__hour

    @hour.setter
    def hour(self, hour):
        if hour:
            self.__hour = int(hour)
        else:
            self.__hour = 0

    @property
    def minute(self):
        return self.__minute

    @minute.setter
    def minute(self, minute):
        if minute:
            self.__minute = int(minute)
        else:
            self.__minute = 0

    @property
    def second(self):
        return self.__second

    @second.setter
    def second(self, second):
        if second:
            self.__second = int(second)
        else:
            self.__second = 0

    @property
    def microsecond(self):
        return self.__microsecond

    @microsecond.setter
    def microsecond(self, microsecond):
        if microsecond:
            self.__microsecond = int(microsecond)
        else:
            self.__microsecond = 0

    def to_dict(self, full=False, date_only=False):
        output = {
            'year': self.year, 'month': self.month, 'day': self.day, 'hour': self.hour, 'minute': self.minute,
            'second': self.second, 'microsecond': self.microsecond
        }
        if full:
            jalali_datetime = self.to_jalali_datetime()
            output['day_name'] = jalali_datetime.strftime("%A")
            output['month_name'] = jalali_datetime.strftime("%B")
        if date_only:
            del output['hour'], output['minute'], output['second'], output['microsecond']
        return output

    def to_unix_timestamp(self, resolution='second'):
        timestamp = self.to_datetime().timestamp()
        if resolution == 'second':
            return int(timestamp)
        elif resolution == 'millisecond':
            return int(timestamp * 1000)
        elif resolution == 'microsecond':
            return int(timestamp * 1000000)
        else:
            raise ValueError(AvishanTranslatable(
                EN='Incorrect resolution. Accepts are "second", "millisecond" and "microsecond". Default is "second".',
                FA='مقیاس نامعتبر. مقادیر قابل قبول: "second"، "millisecond" و "microsecond". مقدار پیش‌فرض "second".'
            ))

    def to_jalali_date(self):
        return JalaliDate(self.year, self.month, self.day)

    def to_jalali_datetime(self):
        return JalaliDatetime(self.year, self.month, self.day, self.hour, self.minute, self.second, self.microsecond)

    def to_date(self):
        return self.to_jalali_date().todate()

    def to_datetime(self) -> datetime:
        return self.to_jalali_datetime().todatetime()

    def to_time(self):
        return self.to_datetime().time()

    def to_str(self, format=None):
        if format is None:
            return str(self.to_jalali_datetime())
        """
        formats: 
        %Y: YYYY year
        %y: YY short year
        %m: MM month
        %d: DD day
        %A: persian weekday دوشنبه
        %a: short persian weekday د 
        %D: ۱۵ day
        %B: persian month شهریور
        %b: short persian month شه
        %N: persian year ۱۳۶۱
        %H: HH hour 24
        %I: II short hour 12 
        %M: MM minute
        %S: SS second
        %f: mmmmmm milliseconds
        %p: ق.ظ ب.ظ
        """
        return self.to_jalali_datetime().strftime(format)

    @staticmethod
    def from_bch_datetime(source):
        return BchDatetime(source.year, source.month, source.day, source.hour, source.minute, source.second,
                           source.microsecond)

    @staticmethod
    def from_dict(source: dict):
        return BchDatetime(
            source.get('year', None), source.get('month', None), source.get('day', None),
            source.get('hour', None), source.get('minute', None), source.get('second', None),
            source.get('microsecond', None),
        )

    @staticmethod
    def from_unix_timestamp(source):
        source = str(source)
        if len(source) > 10:  # todo is it true?
            other = source[10:]
            source = source[:10]
            temp = BchDatetime.from_datetime(datetime.fromtimestamp(int(source)))
            temp.microsecond = other * int(10 ** (6 - len(source)))
            return temp
        return BchDatetime.from_datetime(datetime.fromtimestamp(int(source)))

    @staticmethod
    def from_jalali_datetime(source):
        return BchDatetime(source.year, source.month, source.day, source.hour, source.minute, source.second,
                           source.microsecond)

    @staticmethod
    def from_date(source: date):
        return BchDatetime.from_jalali_datetime(
            JalaliDatetime(datetime.combine(source, time(0, 0, 0, 0)))
        )

    @staticmethod
    def from_datetime(source: datetime):
        return BchDatetime.from_jalali_datetime(JalaliDatetime(source))

    def load_time(self, time: datetime.time):
        self.hour = time.hour
        self.minute = time.minute
        self.second = time.second
        self.microsecond = time.microsecond
        return self

    @staticmethod
    def now():
        return BchDatetime.from_jalali_datetime(JalaliDatetime.now())

    def get_interval_timedelta_from(self, sooner):
        return self - sooner

    def is_today(self):
        now = BchDatetime()
        return now.year == self.year and now.month == self.month and now.day == self.day

    def cleaned_datetime(self, to_forward: bool, force_to_forward: bool = False, years: int = None, months: int = None,
                         days: int = None,
                         hours: int = None, minutes: int = None, seconds: int = None,
                         microseconds: int = None, ) -> 'BchDatetime':
        # todo: complete it
        # todo: if entered amount is 0, change it to 60, or any end
        new = BchDatetime(self)

        if force_to_forward and new.cleaned_datetime(
                to_forward, False, years, months, days, hours, minutes, seconds, microseconds
        ) == new:
            new += 1

        if to_forward:
            if new.microsecond % 1000000 != 0:
                new = new + timedelta(
                    microseconds=(1000000 - new.microsecond % 1000000))
            if new.second % 60 != 0:
                new = new + timedelta(
                    seconds=(60 - new.second % 60))
            if new.minute % minutes != 0:
                new = new + timedelta(minutes=(minutes - (new.minute % minutes)))
        else:
            if new.microsecond % 1000000 != 0:
                new = new - timedelta(
                    microseconds=new.microsecond % 1000000)
            if new.second % 60 != 0:
                new = new - timedelta(
                    seconds=new.second % 60)
            if new.minute % minutes != 0:
                new = new - timedelta(minutes=new.minute % minutes)
        return new

    def __add__(self, other: Union[int, timedelta]) -> 'BchDatetime':
        if isinstance(other, int):
            return BchDatetime.from_jalali_datetime(self.to_jalali_datetime() + timedelta(seconds=other))
        if isinstance(other, timedelta):
            return BchDatetime.from_jalali_datetime(self.to_jalali_datetime() + other)
        raise TypeError(AvishanTranslatable(
            EN='Accepted types are "int" as seconds and "timedelta"',
            FA='مقادیر قابل قبول "int" به عنوان ثانیه ها و "timedelta" هستند'
        ))

    def __sub__(self, other) -> Union[timedelta, 'BchDatetime']:
        if isinstance(other, BchDatetime):
            return self.to_jalali_datetime() - other.to_jalali_datetime()
        if isinstance(other, int):
            return BchDatetime.from_jalali_datetime(self.to_jalali_datetime() - timedelta(seconds=other))
        if isinstance(other, timedelta):
            return BchDatetime.from_jalali_datetime(self.to_jalali_datetime() - other)
        other = BchDatetime(other)
        return self.to_jalali_datetime() - other.to_jalali_datetime()

    # todo: accept more datetime types for add sub and compares
    def __lt__(self, other: 'BchDatetime'):
        return self.to_unix_timestamp('microsecond') < other.to_unix_timestamp('microsecond')

    def __le__(self, other):
        return self.to_unix_timestamp('microsecond') <= other.to_unix_timestamp('microsecond')

    def __gt__(self, other):
        return self.to_unix_timestamp('microsecond') > other.to_unix_timestamp('microsecond')

    def __ge__(self, other):
        return self.to_unix_timestamp('microsecond') >= other.to_unix_timestamp('microsecond')

    def __eq__(self, other):
        return self.to_unix_timestamp('microsecond') == other.to_unix_timestamp('microsecond')

    def __ne__(self, other):
        return self.to_unix_timestamp('microsecond') != other.to_unix_timestamp('microsecond')

    def __str__(self):
        return self.to_datetime().strftime("%Y/%m/%d %H:%M:%S")


class TimeRange(object):

    def __init__(self, start: BchDatetime, end: BchDatetime, belongs_to=None):
        self.start = start
        self.end = end
        self.belongs_to = belongs_to

    @property
    def length(self) -> int:
        return self.end.to_unix_timestamp() - self.start.to_unix_timestamp()

    def __str__(self):
        return str(self.start) + " - " + str(self.end)


class TimeRangeGroup(object):
    # todo 0.2.5: can optimize time ranges to fit together?
    def __init__(self, time_range_group: 'TimeRangeGroup' = None):
        self.time_ranges: List[TimeRange] = []
        if time_range_group:
            for time_range in time_range_group.time_ranges:
                self.time_ranges.append(TimeRange(time_range.start, time_range.end, time_range.belongs_to))
        self.order_time_range_group()

    @property
    def length(self) -> int:
        total = 0
        for time_range in self.time_ranges:
            total += time_range.length
        return total

    @property
    def longest_time_range_seconds(self) -> int:
        longest = 0
        for time_range in self.time_ranges:
            longest = max(longest, time_range.length)
        return longest

    @property
    def longest_time_range(self) -> TimeRange:
        longest = None
        for time_range in self.time_ranges:
            if not longest or time_range.length > longest.length:
                longest = time_range
        return longest

    def clean_with_time_slice(self, minutes: int):
        self.order_time_range_group()
        for time_range in self.time_ranges[:]:
            time_range.start = time_range.start.cleaned_datetime(to_forward=True, minutes=15)
            time_range.end = time_range.end.cleaned_datetime(to_forward=False, minutes=15)

            if time_range.length < minutes * 60:
                self.time_ranges.remove(time_range)
        self.order_time_range_group()

    def order_time_range_group(self):
        self.time_ranges.sort(key=lambda x: x.start)

    def __add__(self, other):
        if isinstance(other, TimeRangeGroup):
            result = TimeRangeGroup(self)
            for other_time_range in other.time_ranges:
                result += other_time_range
            return result

        elif isinstance(other, TimeRange):
            result = TimeRangeGroup(self)
            if len(result.time_ranges) > 0:
                for time_range in result.time_ranges[:]:
                    if time_range.start <= other.start < time_range.end < other.end:
                        result.time_ranges.remove(time_range)
                        result.time_ranges.append(TimeRange(time_range.start, other.end))
                    elif other.start < time_range.start < other.end <= time_range.end:
                        result.time_ranges.remove(time_range)
                        result.time_ranges.append(TimeRange(other.start, time_range.end))
                    elif other.start < time_range.start < time_range.end < other.end:
                        result.time_ranges.remove(time_range)
                        result.time_ranges.append(TimeRange(other.start, other.end))
                    else:
                        result.time_ranges.append(TimeRange(other.start, other.end))
            else:
                result.time_ranges.append(TimeRange(other.start, other.end))
            for time_range in result.time_ranges[:]:
                if time_range.length == 0:
                    result.time_ranges.remove(time_range)
            self.order_time_range_group()
            return result
        raise ValueError()

    def __sub__(self, other):
        if isinstance(other, TimeRangeGroup):
            result = TimeRangeGroup(self)
            for other_time_range in other.time_ranges:
                result -= other_time_range
            return result

        elif isinstance(other, TimeRange):
            for time_range in self.time_ranges[:]:
                if time_range.start < other.start < time_range.end <= other.end:
                    self.time_ranges.remove(time_range)
                    self.time_ranges.append(TimeRange(time_range.start, other.start))
                elif other.start <= time_range.start < other.end < time_range.end:
                    self.time_ranges.remove(time_range)
                    self.time_ranges.append(TimeRange(other.end, time_range.end))
                elif other.start <= time_range.start < time_range.end <= other.end:
                    self.time_ranges.remove(time_range)
                elif time_range.start < other.start < other.end < time_range.end:
                    self.time_ranges.remove(time_range)
                    self.time_ranges.append(TimeRange(time_range.start, other.start))
                    self.time_ranges.append(TimeRange(other.end, time_range.end))

            for time_range in self.time_ranges[:]:
                if time_range.length == 0:
                    self.time_ranges.remove(time_range)
            self.order_time_range_group()
            return self
        raise ValueError()

    def __str__(self):
        total = "["
        for time_range in self.time_ranges:
            total += str(time_range) + "\n"
        total = total[:-1] + "]"
        return total
