from enum import IntEnum

class CustomIntEnum(IntEnum):
    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

    @classmethod
    def get_name(cls, value):
        return cls(value).name