from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable, PermissionDenied, \
    AuthenticationFailed, ValidationError
from rest_framework_jwt.serializers import jwt_encode_handler, jwt_payload_handler
from .models import User


class PasswordLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=32, required=True)
    password = serializers.CharField(max_length=255, required=True)

    def authenticate(self, validated_data):
        username = validated_data['username']
        password = validated_data['password']

        user = User.objects.get(username=username)
        if not user.check_password(password):
            raise AuthenticationFailed(detail='Invalid credentials!')
        
        jwt_token = jwt_encode_handler(jwt_payload_handler(user))
        return user, jwt_token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class SalesManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'password', 'phone', 'salespoint']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'username': {'validators': []}
        }

    def create(self, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        instance = self.Meta.model.objects.create_salesmanager(username, password, **validated_data)
        return instance