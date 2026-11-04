from django.contrib import admin
from organization.models import Site, Department, Designation


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'code', 'is_active', 'created_at')
    list_filter = ('is_active', 'city')
    search_fields = ('name', 'city', 'code', 'address')
    actions = ['delete_selected']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'head_of_department', 'created_at')
    search_fields = ('name', 'code')


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'grade_level')
    list_filter = ('department', 'grade_level')
    search_fields = ('title', 'department__name')
