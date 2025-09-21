from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User


# Category Model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# Movie Model
class Movie(models.Model):
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=100)
    movie_logo = models.FileField()
    description = models.TextField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)

    # NEW: Category ForeignKey (instead of simple charfield)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movies"
    )

    def __str__(self):
        return self.title


# Rating Model
class Myrating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.IntegerField(
        default=0,
        validators=[MaxValueValidator(5), MinValueValidator(0)]
    )

    def __str__(self):
        return f"{self.user} - {self.movie} ({self.rating})"


# Watchlist / MyList
class MyList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    watch = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.movie} - {'Watched' if self.watch else 'Not Watched'}"


# Actor Model
class Actor(models.Model):
    actor_name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to="actor-images/", null=True, blank=True)
    role = models.CharField(max_length=100)
    birth_date = models.DateField(max_length=24)

    def __str__(self):
        return self.actor_name
