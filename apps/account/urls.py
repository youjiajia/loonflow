from django.urls import path
from apps.account.views import LoonAppTokenView, \
    LoonAppTokenDetailView, \
    LoonLoginView, LoonLogoutView

urlpatterns = [
    path('/login', LoonLoginView.as_view()),
    path('/logout', LoonLogoutView.as_view()),
    path('/app_token', LoonAppTokenView.as_view()),
    path('/app_token/<int:app_token_id>', LoonAppTokenDetailView.as_view()),
]
