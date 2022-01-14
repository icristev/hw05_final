from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import POSTS_ON_INDEX

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post


def pagination(request, queryset):
    paginator = Paginator(queryset, POSTS_ON_INDEX)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_namber': page_number,
        'page_obj': page_obj,
    }


def get_page(request, post_list):
    paginator = Paginator(post_list, POSTS_ON_INDEX)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()

    context = {
        'page_obj': get_page(request, posts),
    }

    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()

    context = {
        'group': group,
        'posts': posts,
        'page_obj': get_page(request, posts),
    }

    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    number_of_posts = posts.count()
    context = {
        'page_obj': get_page(request, posts),
        'author': author,
        'posts': posts,
        'number_of_posts': number_of_posts,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comment = post.comments.all()
    form = CommentForm(request.POST or None)
    author = post.author
    context = {
        'post': post,
        'comment': comment,
        'form': form,
        'author': author,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    form = PostForm()

    context = {'form': form}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    template1 = 'posts:post_detail'
    template2 = 'posts/create_post.html'
    if post.author != request.user:
        return redirect(template1, post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect(template1, post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, template2, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    template = 'posts:post_detail'
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(template, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user).all()
    context = pagination(request, post_list)
    template = 'posts/follow.html'
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(
            user=user,
            author=author,
        )
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    template = 'posts:profile'
    get_object_or_404(
        Follow, user=request.user, author__username=username).delete()
    return redirect(template, username=username)
