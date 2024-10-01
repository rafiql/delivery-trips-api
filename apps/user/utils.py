from .config import ROLE_DICT
from apps.trip_management.helpers import get_salespoint_data

def get_user_details(user):
    try:
       
            
        user_response = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'status': user.is_active,
            'role_id': user.role,
            'role': user.get_role_display(),
            'username': user.username,
        }
        if user.role == ROLE_DICT['SalesManager']:
                user_response.update({'salespoint' : get_salespoint_data(user.salespoint),})
        return user_response
    except Exception as e:
        return {}