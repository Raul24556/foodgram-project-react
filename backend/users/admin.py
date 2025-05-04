from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from users.models import User, Follow


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'count_follows', 'count_recipes')
    search_fields = ('username', 'email')

    def count_follows(self, obj):
        return obj.follower.count()
    count_follows.short_description = "Количество подписчиков"

    def count_recipes(self, obj):
        return obj.recipes.count()
    count_recipes.short_description = "Количество рецептов"


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    search_fields = ('user__username', 'following__username')


admin.site.unregister(Group)
