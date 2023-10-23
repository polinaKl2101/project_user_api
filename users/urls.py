from django.urls import path

from users.views import LoginAPIView, VerificationTokenAPIView, UserAPIView

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('verify/<pk>/', VerificationTokenAPIView.as_view(), name='verify'),
    path('user/', UserAPIView.as_view(), name='user'),
]