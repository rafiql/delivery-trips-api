from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied
from apps.user.config import ROLE_DICT


def execute_create(self, validated_data):
    try:
        instance = self.create(validated_data)
    except Exception as e:
        raise ValidationError(detail=str(e))
    return instance


def execute_update(self, instance, validated_data):
    try:
        instance = self.update(instance, validated_data)
    except Exception as e:
        raise ValidationError(detail=str(e))
    return instance

def execute_auth_update(self, instance, validated_data):   
    user = self.context['request'].user
    valid_role = [ ROLE_DICT['Manager'], ROLE_DICT['Admin']]
    if user.role not in valid_role:
        raise PermissionDenied(detail='Permission Denied!')
    try:
        instance = self.update(instance, validated_data)
    except Exception as e:
        raise ValidationError(detail=str(e))
    return instance

class CustomSerializer(serializers.ModelSerializer):

    class Meta:
        model = None
        fields = []

    def create_obj(self, validated_data):
        return execute_create(self, validated_data)

    def update_obj(self, instance, validated_data):
        return execute_update(self, instance, validated_data)

class CustomAuthSerializer(serializers.ModelSerializer):

    class Meta:
        model = None
        fields = []

    def create_obj(self, validated_data):
        return execute_create(self, validated_data)

    def update_obj(self, instance, validated_data):
        return execute_auth_update(self, instance, validated_data)