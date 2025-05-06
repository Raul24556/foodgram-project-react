from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from users.models import User, Follow


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'count_follows', 'count_recipes')
    search_fields = ('username', 'email')

    @admin.display(description="Количество подписчиков")
    def count_follows(self, obj):
        return obj.follower.count()

    @admin.display(description="Количество рецептов")
    def count_recipes(self, obj):
        return obj.recipes.count()


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    search_fields = ('user__username', 'following__username')


admin.site.unregister(Group)
