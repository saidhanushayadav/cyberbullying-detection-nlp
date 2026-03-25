from datetime import datetime
from django.db.models import Q
from django.shortcuts import render, redirect

from cyberbullying.forms import (
    RegistrationForm, LoginForm, CommentForm,
    LikeOrDisLikeForm, PostForm, UpdateProfileForm, UpdatePICForm
)

from cyberbullying.cyberbullying import isBullyingPost, isCyberbullyingPost
from cyberbullying.models import (
    RegistrationModel, CommentModel, LikeOrDisLikeModel,
    PostModel, ShareModel, FriendRequestModel, CyberbullyingModel
)

from cyberbullying.service import getAllPostsByUser, getAllPostsBySearch, getMyFriends


# ===========================
# 🔁 COMMON FUNCTIONS
# ===========================

def increase_cyberbullying_count(username):
    try:
        username = str(username)   # ✅ FORCE STRING

        obj = CyberbullyingModel.objects.filter(username=username).first()

        if obj:
            obj.count = int(obj.count) + 1   # ✅ SAFE INCREMENT
            obj.save()
        else:
            CyberbullyingModel.objects.create(
                username=username,
                count=1
            )

    except Exception as e:
        print("ERROR in increase_cyberbullying_count:", e)


def get_user_with_pic(username):
    user = RegistrationModel.objects.filter(username=username).first()
    if user:
        user.pic = str(user.pic).split("/")[-1]
    return user


def wall_with_msg(request, msg):
    return render(request, "wall.html", {
        "message": msg,
        "posts": getAllPostsByUser(request.session['username'])
    })


# ===========================
# 🧑‍💻 AUTH
# ===========================

def registration(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)

        if form.is_valid():
            username = form.cleaned_data["username"]

            if RegistrationModel.objects.filter(username=username).exists():
                return render(request, 'registration.html', {"message": "User Already Exists"})

            RegistrationModel.objects.create(
                name=form.cleaned_data["name"],
                email=form.cleaned_data["email"],
                mobile=form.cleaned_data["mobile"],
                address=form.cleaned_data["address"],
                username=username,
                password=form.cleaned_data["password"],
                pic=form.cleaned_data["pic"],
                status="yes"
            )

            return render(request, 'index.html', {"message": "Registered Successfully"})

    return render(request, 'registration.html')


def login(request):
    if request.method == "GET":
        form = LoginForm(request.GET)

        if form.is_valid():
            uname = form.cleaned_data["username"]
            upass = form.cleaned_data["password"]

            # ADMIN LOGIN
            if uname == "admin" and upass == "admin":
                request.session['username'] = str(uname)
                request.session['role'] = "admin"

                users = []
                for cyber in CyberbullyingModel.objects.all():
                    user = get_user_with_pic(cyber.username)
                    if user:
                        user.count = cyber.count
                        users.append(user)

                return render(request, "users.html", {"users": users})

            # USER LOGIN
            user = RegistrationModel.objects.filter(
                username=uname, password=upass, status='yes'
            ).first()

            if user:
                request.session['username'] = str(uname)  # ✅ ENSURE STRING
                request.session['role'] = "user"
                return redirect("wall")

    return render(request, 'index.html', {"message": "Invalid Credentials"})


def logout(request):
    request.session.flush()
    return redirect("index")


def activateaccount(request):
    username = request.GET.get('id')
    status = request.GET.get('status')

    RegistrationModel.objects.filter(username=username).update(status=status)

    users = []
    for cyber in CyberbullyingModel.objects.all():
        user = get_user_with_pic(cyber.username)
        if user:
            user.count = cyber.count
            users.append(user)

    return render(request, "users.html", {"users": users})


# ===========================
# 📝 POSTS
# ===========================

def wall(request):
    return render(request, "wall.html", {
        "posts": getAllPostsByUser(request.session['username'])
    })


def getposts(request):
    return wall(request)


def addPost(request):
    form = PostForm(request.POST, request.FILES)

    if form.is_valid():
        title = form.cleaned_data['title']
        image = form.cleaned_data['image']

        if isBullyingPost(title) or isCyberbullyingPost(title):
            increase_cyberbullying_count(request.session['username'])
            return wall_with_msg(request, "⚠️ Bullying content detected")

        PostModel.objects.create(
            username=request.session['username'],
            title=title,
            image=image,
            datetime=datetime.now()
        )

        return wall_with_msg(request, "Posted Successfully")

    return wall_with_msg(request, "Invalid Post")


def deletepost(request):
    post_id = request.GET.get('post')

    PostModel.objects.filter(id=post_id).delete()
    CommentModel.objects.filter(post=post_id).delete()
    LikeOrDisLikeModel.objects.filter(post=post_id).delete()
    ShareModel.objects.filter(post=post_id).delete()

    return redirect("wall")


def sharePost(request):
    ShareModel.objects.create(
        username=request.session['username'],
        post=request.GET.get('postid')
    )
    return redirect("wall")


# ===========================
# 💬 COMMENTS
# ===========================

def postComment(request):
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.cleaned_data['comment']
        post_id = str(request.POST.get('post'))   # ✅ FORCE STRING
        username = str(request.session.get('username'))  # ✅ FORCE STRING

        if isBullyingPost(comment) or isCyberbullyingPost(comment):
            increase_cyberbullying_count(username)
            return wall_with_msg(request, "⚠️ Comment blocked (bullying)")

        CommentModel.objects.create(
            comment=comment,
            username=username,
            post=post_id,
            datetime=datetime.now()
        )

        return wall_with_msg(request, "Comment Added")

    return wall_with_msg(request, "Invalid Comment")


# ===========================
# 👍 LIKE / DISLIKE
# ===========================

def likeOrDisLike(request):
    form = LikeOrDisLikeForm(request.GET)

    if form.is_valid():
        ld = form.cleaned_data['likeOrDislike']
        post_id = form.cleaned_data['post']

        obj, created = LikeOrDisLikeModel.objects.get_or_create(
            username=request.session['username'],
            post=post_id,
            defaults={'status': ld}
        )

        if not created:
            obj.status = ld
            obj.save()

    return redirect("wall")


# ===========================
# 🔍 SEARCH
# ===========================

def search(request):
    return render(request, 'wall.html', {
        'posts': getAllPostsBySearch(request.GET.get("query"))
    })


def searchUsers(request):
    keyword = request.GET.get('keyword')
    friends = getMyFriends(request.session['username'])

    users = RegistrationModel.objects.filter(
        Q(username__icontains=keyword) |
        Q(name__icontains=keyword) |
        Q(email__icontains=keyword) |
        Q(mobile__icontains=keyword)
    )

    results = []
    for user in users:
        if user.username != request.session['username'] and user.username not in friends:
            user.pic = str(user.pic).split("/")[-1]
            results.append(user)

    return render(request, "wall.html", {
        "results": results,
        "posts": getAllPostsByUser(request.session['username'])
    })


# ===========================
# 👥 FRIENDS
# ===========================

def viewfriends(request):
    username = request.session['username']
    friends = getMyFriends(username)

    requests = [
        get_user_with_pic(req.username)
        for req in FriendRequestModel.objects.filter(friendname=username, status='no')
    ]

    friendslist = [
        get_user_with_pic(friend)
        for friend in friends
    ]

    return render(request, "friends.html", {
        "friends": friendslist,
        "requests": requests
    })


def sendFriendRequest(request):
    FriendRequestModel.objects.create(
        username=request.session['username'],
        friendname=request.GET['friendname'],
        datetime=datetime.now(),
        status='no'
    )
    return redirect("viewfriends")


def acceptFriendRequest(request):
    FriendRequestModel.objects.filter(
        username=request.GET['friendname'],
        friendname=request.session['username']
    ).update(status='yes')

    return redirect("viewfriends")


def unFriend(request):
    username = request.session['username']
    friend = request.GET['friendname']

    FriendRequestModel.objects.filter(username=username, friendname=friend).delete()
    FriendRequestModel.objects.filter(username=friend, friendname=username).delete()

    return redirect("viewfriends")


# ===========================
# 👤 PROFILE
# ===========================

def viewprofile(request):
    user = get_user_with_pic(request.session['username'])
    return render(request, 'viewprofile.html', {"profile": user})


def updateprofile(request):
    if request.method == "POST":
        form = UpdateProfileForm(request.POST)
        if form.is_valid():
            RegistrationModel.objects.filter(
                username=request.session['username']
            ).update(**form.cleaned_data)

    return redirect("viewprofile")


def updatepic(request):
    if request.method == "POST":
        form = UpdatePICForm(request.POST, request.FILES)
        if form.is_valid():
            RegistrationModel.objects.filter(
                username=request.session['username']
            ).update(pic=form.cleaned_data["pic"])

    return redirect("viewprofile")