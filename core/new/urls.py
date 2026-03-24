# new/urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('', FeedView.as_view()),
    path('create/', CreatePostView.as_view()),
    path('like/<int:post_id>/', ToggleLikeView.as_view()),
    path('comment/<int:post_id>/', AddCommentView.as_view()),
    path('profile/', UserProfileView.as_view()),
    path('profile/<int:user_id>/', PublicProfileView.as_view()),
    path('follow/<int:user_id>/', ToggleFollowView.as_view()),
]