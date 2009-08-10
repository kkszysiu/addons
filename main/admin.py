from addons.main.models import Category
from addons.main.models import Addon
from addons.main.models import Screenshot
from django.contrib import admin

admin.site.register(Category)
admin.site.register(Addon)
admin.site.register(Screenshot)

