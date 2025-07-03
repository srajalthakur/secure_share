from django.urls import path
from .views import RegisterView, UploadFileView, ListFilesView, GenerateDownloadLink, VerifyEmail, login_view, logout_view, dashboard, home, register, secure_download, ClientEmailLoginRequest, ClientEmailLoginVerify, ops_login_view, client_login_view, OpsEmailLoginVerify

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('signup/', RegisterView.as_view()),
    path('verify-email/<str:token>/', VerifyEmail.as_view()),
    path('upload/', UploadFileView.as_view()),
    path('files/', ListFilesView.as_view()),
    path('download-link/<int:file_id>/', GenerateDownloadLink.as_view()),
    path('secure-download/<str:token>/', secure_download, name='secure_download'),
    # Django template-based views
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    # API for client email login
    path('client-email-login/', ClientEmailLoginRequest.as_view(), name='client_email_login_request'),
    path('client-email-login-verify/<str:token>/', ClientEmailLoginVerify.as_view(), name='client_email_login_verify'),
    # Separate URLs for ops and client login views
    path('login/ops/', ops_login_view, name='ops_login'),
    path('login/client/', client_login_view, name='client_login'),
    # Secure email login verification for ops
    path('ops-email-login-verify/<str:token>/', OpsEmailLoginVerify.as_view(), name='ops_email_login_verify'),
]