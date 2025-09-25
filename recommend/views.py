from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
from django.db.models import Q, Case, When
from .forms import *
from .models import Movie, Myrating, MyList, Category
import pandas as pd


# Home / Index page (फक्त landing page)
def index(request):
    return render(request, "recommend/list.html")


# Movie list with search + category filter
def movie_list(request):
    q = request.GET.get("q", "")
    category = request.GET.get("category", "")

    movies = Movie.objects.all()

    if q:
        movies = movies.filter(Q(title__icontains=q) | Q(description__icontains=q)).distinct()

    if category:
        try:
            movies = movies.filter(category__id=category)
        except:
            movies = movies.filter(category__name__icontains=category)

    categories = Category.objects.all().order_by("name")

    return render(request, "recommend/list.html", {
        "movies": movies,
        "categories": categories,
        "selected_category": category,
        "q": q,
    })


# Show details of the movie
def detail(request, movie_id):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404
    movies = get_object_or_404(Movie, id=movie_id)
    movie = Movie.objects.get(id=movie_id)

    temp = list(MyList.objects.all().values().filter(movie_id=movie_id, user=request.user))
    if temp:
        update = temp[0]['watch']
    else:
        update = False

    if request.method == "POST":
        # For my list
        if 'watch' in request.POST:
            watch_flag = request.POST['watch']
            update = True if watch_flag == 'on' else False

            if MyList.objects.filter(movie_id=movie_id, user=request.user).exists():
                MyList.objects.filter(movie_id=movie_id, user=request.user).update(watch=update)
            else:
                q = MyList(user=request.user, movie=movie, watch=update)
                q.save()

            if update:
                messages.success(request, "Movie added to your list!")
            else:
                messages.success(request, "Movie removed from your list!")

        # For rating
        else:
            rate = request.POST['rating']
            if Myrating.objects.filter(movie_id=movie_id, user=request.user).exists():
                Myrating.objects.filter(movie_id=movie_id, user=request.user).update(rating=rate)
            else:
                q = Myrating(user=request.user, movie=movie, rating=rate)
                q.save()

            messages.success(request, "Rating has been submitted!")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    out = list(Myrating.objects.filter(user=request.user.id).values())

    movie_rating = 0
    rate_flag = False
    for each in out:
        if each['movie_id'] == movie_id:
            movie_rating = each['rating']
            rate_flag = True
            break

    context = {
        'movies': movies,
        'movie_rating': movie_rating,
        'stars': range(1, 6),
        'rate_flag': rate_flag,
        'update': update,
    }
    return render(request, 'recommend/detail.html', context)


# MyList functionality
def watch(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404

    movies = Movie.objects.filter(mylist__watch=True, mylist__user=request.user)
    q = request.GET.get('q', '')

    if q:
        movies = movies.filter(Q(title__icontains=q)).distinct()

    return render(request, 'recommend/watch.html', {'movies': movies})


# Similarity helper
def get_similar(movie_name, rating, corrMatrix):
    similar_ratings = corrMatrix[movie_name] * (rating - 2.5)
    similar_ratings = similar_ratings.sort_values(ascending=False)
    return similar_ratings


# Recommendation Algorithm
def recommend(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404

    movie_rating = pd.DataFrame(list(Myrating.objects.all().values()))
    new_user = movie_rating.user_id.unique().shape[0]
    current_user_id = request.user.id

    if current_user_id > new_user:
        movie = Movie.objects.get(id=19)
        q = Myrating(user=request.user, movie=movie, rating=0)
        q.save()

    userRatings = movie_rating.pivot_table(index=['user_id'], columns=['movie_id'], values='rating')
    userRatings = userRatings.fillna(0, axis=1)
    corrMatrix = userRatings.corr(method='pearson')

    user = pd.DataFrame(list(Myrating.objects.filter(user=request.user).values())).drop(['user_id', 'id'], axis=1)
    user_filtered = [tuple(x) for x in user.values]
    movie_id_watched = [each[0] for each in user_filtered]

    similar_movies = pd.DataFrame()
    for movie, rating in user_filtered:
        similar_movies = pd.concat([similar_movies, get_similar(movie, rating, corrMatrix)], axis=1)

    movies_id = list(similar_movies.sum(axis=1).sort_values(ascending=False).index)
    movies_id_recommend = [each for each in movies_id if each not in movie_id_watched]
    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(movies_id_recommend)])
    movie_list = list(Movie.objects.filter(id__in=movies_id_recommend).order_by(preserved)[:10])

    context = {'movie_list': movie_list}
    return render(request, 'recommend/recommend.html', context)


# Register user
def signUp(request):
    form = UserForm(request.POST or None)

    if form.is_valid():
        user = form.save(commit=False)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user.set_password(password)
        user.save()
        user = authenticate(username=username, password=password)

        if user is not None and user.is_active:
            login(request, user)
            return redirect("index")

    context = {'form': form}
    return render(request, 'recommend/signUp.html', context)


# Login User
def Login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect("index")
            else:
                return render(request, 'recommend/login.html', {'error_message': 'Your account disable'})
        else:
            return render(request, 'recommend/login.html', {'error_message': 'Invalid Login'})

    return render(request, 'recommend/login.html')


# Logout user
def Logout(request):
    logout(request)
    return redirect("login")
