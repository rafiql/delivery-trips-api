from apps.base.utils import dict_to_choice

ROLE_DICT_MANAGER = {
    'SalesManager': 3,
}

ROLE_DICT = {
    'Admin':1,
    'Manager': 2,
    'SalesManager': 3,
}

ROLE_CHOICES = dict_to_choice(ROLE_DICT)

def get_role_key_value(given_value):
    ROLE_DICT = {
        1:'Admin',
        2: 'Manager',
        3: 'SalesManager',
    }
    if given_value in ROLE_DICT.keys():
        return ROLE_DICT[given_value]
    return None