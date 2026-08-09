"""Django admin panelining umumiy ko'rinishi.

apps.common INSTALLED_APPS da bo'lgani uchun Django bu modulni
avtomatik yuklaydi — alohida import qilish shart emas.
"""
from django.contrib import admin

admin.site.site_header = "SMART FLEET"
admin.site.site_title = "SMART FLEET boshqaruv"
admin.site.index_title = "Boshqaruv paneli"
