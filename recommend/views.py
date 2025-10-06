from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Case, When
from .models import Movie, Myrating, MyList, Category
from .forms import UserForm
import pandas as pd

# ------------------------
# Home Page
# ------------------------
def index(request):
    return render(request, "recommend/list.html")

# ------------------------
# Movie List
# ------------------------
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

# ------------------------
# Movie Detail (Rating + Watchlist)
# ------------------------
@login_required
def detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    # Watchlist
    mylist_entry = MyList.objects.filter(movie=movie, user=request.user).first()
    update = mylist_entry.watch if mylist_entry else False

    # Rating
    myrating_entry = Myrating.objects.filter(movie=movie, user=request.user).first()
    movie_rating = myrating_entry.rating if myrating_entry else 0
    rate_flag = True if myrating_entry else False

    if request.method == "POST":
        if 'watch' in request.POST:
            watch_flag = request.POST.get('watch') == 'on'
            if mylist_entry:
                mylist_entry.watch = watch_flag
                mylist_entry.save()
            else:
                MyList.objects.create(user=request.user, movie=movie, watch=watch_flag)
            update = watch_flag
            msg = "added to" if update else "removed from"
            messages.success(request, f"Movie {msg} your list!")

        elif 'rating' in request.POST:
            rating_value = int(request.POST.get('rating', 0))
            if myrating_entry:
                myrating_entry.rating = rating_value
                myrating_entry.save()
            else:
                Myrating.objects.create(user=request.user, movie=movie, rating=rating_value)
            movie_rating = rating_value
            rate_flag = True
            messages.success(request, "Rating has been submitted!")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    context = {
        'movies': movie,
        'movie_rating': movie_rating,
        'rate_flag': rate_flag,
        'update': update,
        'stars': range(1, 6)
    }
    return render(request, 'recommend/detail.html', context)

# ------------------------
# Watchlist Page
# ------------------------
@login_required
def watch(request):
    movies = Movie.objects.filter(mylist__watch=True, mylist__user=request.user)
    q = request.GET.get('q', '')
    if q:
        movies = movies.filter(Q(title__icontains=q)).distinct()
    return render(request, 'recommend/watch.html', {'movies': movies})

# ------------------------
# Recommendation
# ------------------------
@login_required
def recommend(request):
    movie_rating_df = pd.DataFrame(list(Myrating.objects.all().values()))
    current_user_id = request.user.id

    if current_user_id > movie_rating_df.user_id.nunique():
        movie = Movie.objects.first()
        Myrating.objects.create(user=request.user, movie=movie, rating=0)

    userRatings = movie_rating_df.pivot_table(index='user_id', columns='movie_id', values='rating').fillna(0)
    corrMatrix = userRatings.corr(method='pearson')

    user_ratings = movie_rating_df[movie_rating_df.user_id == request.user.id][['movie_id', 'rating']]
    watched_movies = user_ratings['movie_id'].tolist()

    similar_movies_df = pd.DataFrame()
    for _, row in user_ratings.iterrows():
        similar_movies_df = pd.concat([similar_movies_df, corrMatrix[row['movie_id']] * (row['rating'] - 2.5)], axis=1)

    recommended_movie_ids = list(similar_movies_df.sum(axis=1).sort_values(ascending=False).index)
    recommended_movie_ids = [mid for mid in recommended_movie_ids if mid not in watched_movies]

    preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(recommended_movie_ids)])
    recommended_movies = Movie.objects.filter(id__in=recommended_movie_ids).order_by(preserved_order)[:10]

    return render(request, 'recommend/recommend.html', {'movie_list': recommended_movies})

# ------------------------
# SignUp / Login / Logout
# ------------------------
def signUp(request):
    form = UserForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user and user.is_active:
            login(request, user)
            return redirect("index")
    return render(request, 'recommend/signUp.html', {'form': form})

def Login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return redirect("index")
            else:
                return render(request, 'recommend/login.html', {'error_message': 'Account disabled'})
        else:
            return render(request, 'recommend/login.html', {'error_message': 'Invalid login'})
    return render(request, 'recommend/login.html')

@login_required
def Logout(request):
    logout(request)
    return redirect("login")
