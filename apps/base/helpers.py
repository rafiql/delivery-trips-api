from django.db.models.fields import FloatField
from rest_framework.pagination import LimitOffsetPagination
from itertools import chain

def get_paginated(queryset, request, to_dict, limit=10):
    paginator = LimitOffsetPagination()
    paginator.max_limit = 50
    paginator.default_limit = limit
    paginator.offset = 0

    obj_list = paginator.paginate_queryset(
        queryset,
        request
    )

    results = to_dict(obj_list)

    next_link = paginator.get_next_link()
    prev_link = paginator.get_previous_link()
    if next_link:
        next_link = next_link.split('?')[1]
    if prev_link:
        prev_link = prev_link.split('?')[1]

    data = {
        'results': results,
        'limit': paginator.limit,
        'offset': paginator.offset,
        'count': paginator.count,
        'next': next_link,
        'prev': prev_link,
    }

    # print(json.dumps(data))

    return data


def inc_field(obj, field_name, field_val):
    # model.objects.filter(id=obj.id).update(
    #     **{field_name: getattr(obj, field_name) + field_val}
    # )

    setattr(obj, field_name, getattr(obj, field_name) + field_val)
    obj.save()


def to_dict(instance):
    opts = instance._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields):
        if f.__class__ is FloatField:
            data[f.name] = round(float(f.value_from_object(instance)),2)
        else:
            data[f.name] = f.value_from_object(instance)
    for f in opts.many_to_many:
        data[f.name] = [i.id for i in f.value_from_object(instance)]
    return data