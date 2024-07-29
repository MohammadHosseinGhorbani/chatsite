from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Message, Room, Member, User


class MemberInline(admin.StackedInline):
    verbose_name = "Membership"
    model = Member
    extra = 0


class UserAdmin(BaseUserAdmin):
    old_fieldsets = BaseUserAdmin.fieldsets

    fieldsets = old_fieldsets[:2] + (("Login Details", {"fields": ["telegram_id", "login_code", "passed_login_code"]}),) + old_fieldsets[2:]
    inlines = BaseUserAdmin.inlines + (MemberInline,)


admin.site.register(Message)
admin.site.register(Room)
admin.site.register(Member)
admin.site.register(User, UserAdmin)

