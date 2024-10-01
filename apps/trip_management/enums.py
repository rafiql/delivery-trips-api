import enum

from apps.base.enums import CustomIntEnum


class MapProviderEnum(CustomIntEnum):
    DingiMap = 1
    GoogleMap = 2
    Both = 3


class MapApiProviderEnum(CustomIntEnum):
    DingiMap = 1
    GoogleMap = 2