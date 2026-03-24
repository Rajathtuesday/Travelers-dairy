# new/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import get_object_or_404
from django.db.models import F

from .models import *
from .serializers import *


# =========================
# PAGINATION
# =========================
class FeedPagination(PageNumberPagination):
    page_size = 10


# =========================
# FEED
# =========================
class FeedView(generics.ListAPIView):
    queryset = Post.objects.select_related('user', 'location').prefetch_related('images', 'comments')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = FeedPagination


# =========================
# CREATE POST
# =========================
class CreatePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        title = request.data.get('title')
        description = request.data.get('description')
        location_name = request.data.get('location')

        if not title or not description or not location_name:
            return Response({"error": "Missing fields"}, status=400)

        location, _ = Location.objects.get_or_create(
            name=location_name.strip().title(),
            country="Unknown"
        )

        post = Post.objects.create(
            user=request.user,
            title=title,
            description=description,
            location=location,
        )

        images = request.FILES.getlist('images')
        for img in images:
            PostImage.objects.create(post=post, image=img)

        self.assign_badges(request.user, location)

        return Response(PostSerializer(post).data, status=201)

    def assign_badges(self, user, location):
        badges = Badge.objects.filter(location=location)

        for badge in badges:
            UserBadge.objects.get_or_create(user=user, badge=badge)


# =========================
# LIKE / UNLIKE (SAFE)
# =========================
class ToggleLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if not created:
            like.delete()
            Post.objects.filter(id=post_id).update(likes_count=F('likes_count') - 1)
            return Response({'liked': False})

        Post.objects.filter(id=post_id).update(likes_count=F('likes_count') + 1)
        return Response({'liked': True})


# =========================
# COMMENT
# =========================
class AddCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        content = request.data.get('content')
        if not content:
            return Response({"error": "Content required"}, status=400)

        comment = Comment.objects.create(
            user=request.user,
            post=post,
            content=content,
            parent_id=request.data.get('parent')
        )

        return Response(CommentSerializer(comment).data, status=201)


# =========================
# USER PROFILE
# =========================
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        posts = Post.objects.filter(user=user)
        badges = UserBadge.objects.filter(user=user)

        return Response({
            "user": UserSerializer(user).data,
            "posts": PostSerializer(posts, many=True).data,
            "badges": UserBadgeSerializer(badges, many=True).data
        })


# =========================
# FOLLOW
# =========================
class ToggleFollowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        if target_user == request.user:
            return Response({"error": "Cannot follow yourself"}, status=400)

        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target_user
        )

        if not created:
            follow.delete()
            return Response({'following': False})

        return Response({'following': True})


# =========================
# PUBLIC PROFILE
# =========================
class PublicProfileView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        posts = Post.objects.filter(user=user)
        badges = UserBadge.objects.filter(user=user)

        return Response({
            "user": UserSerializer(user).data,
            "posts": PostSerializer(posts, many=True).data,
            "badges": UserBadgeSerializer(badges, many=True).data
        })