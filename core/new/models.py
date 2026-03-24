# new/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# =========================
# LOCATION MODEL
# =========================
class Location(models.Model):
    name = models.CharField(max_length=150)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        unique_together = ['name', 'country', 'state']
        ordering = ['country', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.country}-{self.state}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, {self.country}"


# =========================
# USER PROFILE (EXTENSION)
# =========================
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# =========================
# POST MODEL (CORE)
# =========================
class Post(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')

    title = models.CharField(max_length=200)
    description = models.TextField()

    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='posts')

    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')

    likes_count = models.PositiveIntegerField(default=0)  # denormalized for performance

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['location']),
        ]

    def __str__(self):
        return self.title


# =========================
# POST IMAGES (MULTIPLE)
# =========================
class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='posts/gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


# =========================
# LIKES SYSTEM
# =========================
class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']


# =========================
# COMMENTS SYSTEM
# =========================
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    class Meta:
        ordering = ['created_at']


# =========================
# BADGE SYSTEM
# =========================
class Badge(models.Model):
    BADGE_TYPE = [
        ('location', 'Location Based'),
        ('milestone', 'Milestone'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()

    icon = models.ImageField(upload_to='badges/')

    badge_type = models.CharField(max_length=20, choices=BADGE_TYPE, default='location')

    # Rule: based on location
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True)

    # Rule: milestone (e.g. 10 posts)
    required_posts = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =========================
# USER BADGES (MAPPING)
# =========================
class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)

    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'badge']


# =========================
# FOLLOW SYSTEM (SOCIAL)
# =========================
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']