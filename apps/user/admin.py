from django.apps import apps
from django.contrib import admin

# Register your models here.

app_models = apps.get_app_config('user').get_models()
admin.site.register(list(app_models))