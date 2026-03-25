from django.db.models import Q
from cyberbullying.beans import PostBean
from cyberbullying.models import (
    LikeOrDisLikeModel,
    CommentModel,
    PostModel,
    ShareModel,
    FriendRequestModel
)
from cyberbullying.sentimentanalyzer import getCommentSentiment


def getPostBeanById(postid):

    post = PostModel.objects.get(id=postid)

    if post.image:
        post.image = str(post.image).split("/")[-1]

    comments = CommentModel.objects.filter(post=post.id)

    likes = 0
    dislikes = 0

    for react in LikeOrDisLikeModel.objects.filter(post=post.id):
        if int(react.status) == 0:
            dislikes += 1
        elif int(react.status) == 1:
            likes += 1

    positive = negative = neutral = 0

    for comment in comments:
        sentiment = getCommentSentiment(comment.comment)

        if sentiment == "positive":
            positive += 1
        elif sentiment == "negative":
            negative += 1
        else:
            neutral += 1

    return PostBean(
        post,
        comments,
        likes,
        dislikes,
        positive,
        negative,
        neutral
    )


def getAllPosts():

    posts = []

    for post in PostModel.objects.all().order_by('-datetime'):
        if not post.isbullyingpost:   # FIX HERE
            posts.append(getPostBeanById(post.id))

    return posts


def getAllPostsByUser(username):

    posts = []

    friends = getMyFriends(username)
    friends.add(username)

    friends = list(friends)

    for post in PostModel.objects.filter(
            username__in=friends).order_by('-datetime'):
        posts.append(getPostBeanById(post.id))

    for share in ShareModel.objects.filter(username__in=friends):
        posts.append(getPostBeanById(share.post))

    return posts


def getAllPostsBySearch(keyword):

    posts = []

    if not keyword:
        return posts

    keyword = keyword.strip()

    queryset = PostModel.objects.filter(
        Q(title__icontains=keyword) |
        Q(username__icontains=keyword)
    ).order_by('-datetime')

    for post in queryset:
        if not post.isbullyingpost:   # FIX HERE
            posts.append(getPostBeanById(post.id))

    print("Search results:", len(posts))
    return posts


def getMyFriends(username):

    friends = set()

    for req in FriendRequestModel.objects.filter(
            username=username, status="yes"):
        friends.add(req.friendname)

    for req in FriendRequestModel.objects.filter(
            friendname=username, status="yes"):
        friends.add(req.username)

    return friends
