from django.contrib import admin
from .models import Movie, Category, Myrating, MyList, Actor


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'release_date')
    list_filter = ('category',)
    search_fields = ('title',)


@admin.register(Myrating)
class MyratingAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'rating')
    list_filter = ('rating', 'movie', 'user')
    search_fields = ('user__username', 'movie__title')


@admin.register(MyList)
class MyListAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'watch')
    list_filter = ('watch',)
    search_fields = ('user__username', 'movie__title')


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('actor_name', 'role', 'birth_date')
    search_fields = ('actor_name', 'role')
