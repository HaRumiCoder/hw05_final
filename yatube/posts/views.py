from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow
from .settings import POST_PER_PAGE


def paginator_obj(obj, obj_per_page, request):
    return Paginator(obj, obj_per_page).get_page(request.GET.get("page"))


def index(request):
    return render(request, "posts/index.html", {
        "page_obj": paginator_obj(Post.objects.all(), POST_PER_PAGE, request)
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, "posts/group_list.html", {
        "group": group,
        "page_obj": paginator_obj(group.posts.all(), POST_PER_PAGE, request),
    })


def profile(request, username):
    user = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and (
        set(user.following.all()) | set(request.user.follower.all())
    )
    context = {
        "page_obj": paginator_obj(user.posts.all(), POST_PER_PAGE, request),
        "author": user,
        "following": following
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    return render(request, "posts/post_detail.html", {
        "post": get_object_or_404(Post, pk=post_id),
        "form": CommentForm(request.POST or None)
    })


@login_required
def create_post(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, "posts/create_post.html", {"form": form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("posts:profile", post.author.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        return render(request, "posts/create_post.html", {
            "is_edit": True,
            "post": post,
            "form": form
        })
    form.save()
    return redirect("posts:post_detail", post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    return render(request, 'posts/follow.html', {
        'page_obj': paginator_obj(posts, POST_PER_PAGE, request)
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if (request.user.username != username
            and not request.user.follower.filter(author=author).exists()):
        Follow.objects.create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow,
        user=request.user,
        author__username=username).delete()
    return redirect('posts:profile', username)
