from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.user.models import User
from apps.user.config import ROLE_DICT
from apps.user.permission import IsSuperUser
from apps.user.serializers import PasswordLoginSerializer, SalesManagerSerializer
from apps.user.utils import get_user_details


class SalesManagerSignup(APIView):
    permission_classes = (IsSuperUser,)
    ObjModel = User

    def post(self, request, format=None):
        """
        Sample Submit:
        ---
            {
                'username': 'username', 
                'first_name': 'first_name', 
                'last_name': 'last_name', 
                'password': 'password', 
                'phone': '0171700000', 
                'salespoint': '1'
            }

        Sample Response:
        ---
            {
                'user': { profile fields },
            }

        """
        serializer = SalesManagerSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.create(serializer.validated_data)
            data = {
                'user': get_user_details(user),
            }
            return Response(data, status=200)
        return Response({'detail': str(serializer.errors)}, status=400)

    def get(self, request, format=None):
        
        result=[]
        extra_fields = request.query_params
        obj_qs = self.ObjModel.objects.filter(role=ROLE_DICT['SalesManager'])
        if extra_fields:
            obj_qs = obj_qs.filter(**extra_fields)

        if len(obj_qs) < 1:
            resp = {'detail': "Object not found."}
            return Response(resp, status=400)
        for obj in obj_qs:
                result.append(get_user_details(obj))
        return Response(result, status=200)

    def patch(self, request, pk, format=None):
        obj_instance = self.ObjModel.objects.filter(id=pk, role=ROLE_DICT['SalesManager'])
        if len(obj_instance) > 0:
            obj_instance = obj_instance[0]
        else: 
            return Response({'detail': 'id:' + str(pk) + " not found" }, status=200)
        serializer = SalesManagerSerializer(data=request.data)
        self.check_object_permissions(request, obj_instance)
        if serializer.is_valid():
            password = serializer.validated_data.pop('password', None)
            if password is not None:
                obj_instance.set_password(password)
            obj_instance = serializer.update(
                 obj_instance, serializer.validated_data
                )
            data = {
                'user': get_user_details(obj_instance),
            }
            return Response(data, status=200)
        return Response({'detail': str(serializer.errors)}, status=400)
    
    def delete(self, request, pk, format=None):
        obj_qs = self.ObjModel.objects.filter(id=pk, role=ROLE_DICT['SalesManager'])

        if len(obj_qs) > 0:
            obj_instance = obj_qs[0]
            self.check_object_permissions(request, obj_instance)
            try:
                obj_instance.delete()
                return Response({'msg': 'OK'}, status=200)
            except Exception as e:
                return Response({'details': str(e)}, status=400)
        return Response({'details': 'Object not found!'}, status=400)



class PasswordLogin(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        """
        Sample Submit:
        ---
            {
                'username': 'xyz',
                'password': 'asdfasdfasdf2',
            }
        Sample Response:
        ---
            {
                'user_details': { profile fields },
                'jwt_token': jwt_token,
            }
        """
        serializer = PasswordLoginSerializer(data=request.data)
        if serializer.is_valid():
            user, jwt_token = serializer.authenticate(serializer.validated_data)
            data = {
                'user_details': get_user_details(user),
                'jwt_token': jwt_token,
            }
            return Response(data, status=200)
        # request_logger.info(f'{get_client_ip(request)}, {serializer.errors}')
        return Response({'detail': str(serializer.errors)}, status=400)
