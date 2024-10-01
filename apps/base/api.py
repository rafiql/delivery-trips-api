from rest_framework import viewsets
from rest_framework.exceptions import NotAcceptable
from rest_framework.response import Response
from rest_framework.decorators import action

from apps.base.helpers import get_paginated
from apps.user.config import ROLE_DICT

"""
Generic ViewSet Template
"""


class CustomViewSet(viewsets.ViewSet):
    """
    retrieve:
        Return single object

        Sample Response:
        ---
            {
            }

    list:
        Return object list

        Query parameters:
        ---
            token:
                type: str
                required: No

        Sample Response:
        ---
            [
                {
                },.....
            ]

    create:
        Create object

        Sample Submit:
        ---
            {
            }

    partial_update:
        Update single object

        Sample Submit:
        ---
            {
            }

    paginated:
        Return paginated object list

        Sample response:
        ---
            {
                'limit': 10,
                'offset': 20,
                'count': 101,
                'next': 'limit=5&offset=30',
                'prev': 'limit=5&offset=10',
                'results': [
                    {},...
                ]
            }
    search:
        can filter or search with permitted fields

        Sample response:
        ---
            {
            }
    """

    ObjModel = None
    ObjSerializer = None
    ObjSearchFields = []
    ObjGetSearchFields = []

    def obj_filter(self, request):
        return self.ObjModel.objects.all()

    def extra_filter_single(self, obj_qf):
        return obj_qf

    def extra_filter_list(self, obj_qf):
        return obj_qf

    def get_obj_details(self, obj):
        serializer = self.ObjSerializer(obj)
        return serializer.data

    def get_dict_list(self, obj_qs):
        obj_dict_list = []
        for obj in obj_qs:
            obj_details = self.get_obj_details(obj)
            obj_dict_list.append(obj_details)
        return obj_dict_list
    
    def search_queryset(self, request, fields_only=None):
        queryset = self.obj_filter(request)
        filter_args = {}
        for param in request.query_params:
            for field in self.ObjSearchFields:
                if param.startswith(field):
                    filter_args[param] = request.query_params[param]
        if fields_only is not None:
            results = queryset.only(*fields_only).filter(**filter_args)
        else:
            results = queryset.filter(**filter_args)
        return results

    def retrieve(self, request, pk, format=None):

        obj_qs = self.ObjModel.objects.filter(id=pk)
        obj_qs = self.extra_filter_single(obj_qs)
        if len(obj_qs) < 1:
            resp = {'detail': "Object not found."}
            return Response(resp, status=400)
        obj_instance = obj_qs[0]
        self.check_object_permissions(request, obj_instance)
        obj_details = self.get_obj_details(obj_instance)
        return Response(obj_details, status=200)

    def list(self, request, format=None):

        obj_list_qs = self.obj_filter(request)
        obj_list_qs = self.extra_filter_list(obj_list_qs)
        obj_list = self.get_dict_list(obj_list_qs)
        return Response(obj_list, status=200)

    def create(self, request, format=None):
        if request.user.role == ROLE_DICT['SalesManager']:
            raise NotAcceptable(detail='User not have proper permission')   
        serializer = self.ObjSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            obj_instance = serializer.create_obj(serializer.validated_data)
            data = self.get_obj_details(obj_instance)
            return Response(data, status=201)
        return Response(serializer.errors, status=400)

    def partial_update(self, request, pk, format=None):
        if request.user.role == ROLE_DICT['SalesManager']:
            raise NotAcceptable(detail='User not have proper permission.')   
        obj_qs = self.ObjModel.objects.filter(id=pk)
        if len(obj_qs) > 0:
            obj_instance = obj_qs[0]
            serializer = self.ObjSerializer(
                data=request.data,
                context={'request': request, 'view': self}
            )
            self.check_object_permissions(request, obj_instance)
            if serializer.is_valid():
                obj_instance = serializer.update_obj(
                    obj_instance, serializer.validated_data
                )
                data = self.get_obj_details(obj_instance)
                return Response(data, status=200)
            return Response(serializer.errors, status=400)
        return Response({'details': 'Object not found!'}, status=400)

    def destroy(self, request, pk, format=None):
        if request.user.role == ROLE_DICT['SalesManager']:
            raise NotAcceptable(detail='User not have proper permission.')   
        obj_qs = self.ObjModel.objects.filter(id=pk)

        if len(obj_qs) > 0:
            obj_instance = obj_qs[0]
            self.check_object_permissions(request, obj_instance)
            try:
                obj_instance.delete()
                return Response({'msg': 'OK'}, status=200)
            except Exception as e:
                return Response({'details': str(e)}, status=400)
        return Response({'details': 'Object not found!'}, status=400)

    @action(methods=['get'], detail=False)
    def paginated(self, request):
        obj_list_qs = self.obj_filter(request)
        obj_list = get_paginated(
            obj_list_qs,
            request,
            self.get_dict_list
        )
        return Response(obj_list, status=200)
    
    @action(methods=['get'], detail=False)
    def search(self, request):
        obj_list = self.search_queryset(request, fields_only=self.ObjGetSearchFields \
                                                 if self.ObjGetSearchFields else None)
        obj_list = obj_list.values(*self.ObjGetSearchFields)
        return Response(obj_list, status=200)
