from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from .forms import LoginForm, FileUploadForm, RegisterForm
from django.db.models import Q
from django.http import HttpResponseRedirect

# Create your views here.
from django.http import JsonResponse, HttpResponseForbidden
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, FileUploadSerializer
from .models import UploadedFile, User
from itsdangerous import URLSafeSerializer
from django.conf import settings
from django.core.mail import send_mail
from django.http import FileResponse
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from django.views.decorators.csrf import csrf_exempt

SECRET = 'mysecretkey123'  # Use env in production
serializer = URLSafeSerializer(SECRET)

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        user = User.objects.get(username=response.data['username'])
        token = serializer.dumps({'user_id': user.id})
        # url = f"http://127.0.0.1:8000/verify-email/{token}"
        send_mail("Verify your Email", "Click the link to verify your email.", 'admin@test.com', [user.email])
        return Response({'message': 'Registered. Check email.'})

class VerifyEmail(APIView):
    def get(self, request, token):
        try:
            data = serializer.loads(token)
            user = User.objects.get(id=data['user_id'])
            user.is_active = True
            user.save()
            return Response({"message": "Email verified"})
        except:
            return Response({"error": "Invalid token"}, status=400)

class UploadFileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_ops:
            return Response({"error": "Only Ops can upload."}, status=403)
        file = request.FILES['file']
        if not file.name.endswith(('docx', 'pptx', 'xlsx')):
            return Response({"error": "Invalid file type"}, status=400)
        obj = UploadedFile.objects.create(user=request.user, file=file)
        return Response({"message": "File uploaded", "id": obj.id})

class ListFilesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        files = UploadedFile.objects.all()
        return Response([{"id": f.id, "file": f.file.url} for f in files])

class GenerateDownloadLink(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, file_id):
        if not request.user.is_client:
            return Response({"error": "Only client users can access this."}, status=403)
        token = serializer.dumps({'file_id': file_id, 'user_id': request.user.id})
        # link = f"http://127.0.0.1:8000/secure-download/{token}"
        return Response({"download-link": token, "message": "success"})

@login_required
def secure_download(request, token):
    try:
        data = serializer.loads(token)
        if request.user.id != data['user_id']:
            return HttpResponseForbidden("Access denied")
        if hasattr(request.user, 'is_ops') and request.user.is_ops:
            return HttpResponseForbidden("Ops users are not allowed to download files.")
        file = UploadedFile.objects.get(id=data['file_id'])
        return FileResponse(file.file)
    except Exception:
        return HttpResponseForbidden("Invalid or expired link")
        

def root_view(request):
    return HttpResponseRedirect('/api/')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'api/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    user = request.user
    user_type = 'Ops User' if user.is_ops else ('Client User' if user.is_client else 'User')
    if request.method == 'POST':
        upload_form = FileUploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            file_obj = upload_form.save(commit=False)
            file_obj.user = user
            if user.is_ops:
                if not file_obj.file.name.endswith(('docx', 'pptx', 'xlsx')):
                    messages.error(request, 'Invalid file type.')
                else:
                    file_obj.save()
                    messages.success(request, 'File uploaded successfully!')
            else:
                messages.error(request, 'Only Ops users can upload files.')
        else:
            messages.error(request, 'Upload failed.')
    else:
        upload_form = FileUploadForm()
    files = UploadedFile.objects.all()
    secure_links = {}
    if user.is_client:
        for file in files:
            token = serializer.dumps({'file_id': file.id, 'user_id': user.id})
            url = request.build_absolute_uri(f"/api/secure-download/{token}/")
            secure_links[file.id] = url
    return render(request, 'api/dashboard.html', {
        'user': user,
        'user_type': user_type,
        'upload_form': upload_form,
        'files': files,
        'secure_links': secure_links
    })

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # Ensure user can log in immediately
            user.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'api/register.html', {'form': form})

@csrf_protect
def home(request):
    user = request.user
    user_type = 'Ops User' if user.is_authenticated and user.is_ops else ('Client User' if user.is_authenticated and user.is_client else 'User')
    login_form = LoginForm(request, data=request.POST or None)
    upload_form = FileUploadForm()
    files = UploadedFile.objects.all()
    share_link = None
    secure_links = {}
    if user.is_authenticated and user.is_client:
        for file in files:
            token = serializer.dumps({'file_id': file.id, 'user_id': user.id})
            url = request.build_absolute_uri(f"/api/secure-download/{token}/")
            secure_links[file.id] = url
    if not user.is_authenticated:
        if request.method == 'POST':
            if login_form.is_valid():
                login(request, login_form.get_user())
                user = login_form.get_user()
                if hasattr(user, 'is_ops') and user.is_ops:
                    return redirect('dashboard')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        return render(request, 'api/home.html', {'login_form': login_form, 'files': files})
    else:
        if request.method == 'POST' and 'file' in request.FILES:
            upload_form = FileUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                file_obj = upload_form.save(commit=False)
                file_obj.user = user
                if user.is_ops:
                    if not file_obj.file.name.endswith(('docx', 'pptx', 'xlsx')):
                        messages.error(request, 'Invalid file type.')
                    else:
                        file_obj.save()
                        messages.success(request, 'File uploaded successfully!')
                else:
                    messages.error(request, 'Only Ops users can upload files.')
            else:
                messages.error(request, 'Upload failed.')
        files = UploadedFile.objects.all()
        print('DEBUG: secure_links =', secure_links)
        return render(request, 'api/home.html', {
            'user': user,
            'user_type': user_type,
            'upload_form': upload_form,
            'files': files,
            'share_link': share_link,
            'secure_links': secure_links
        })

# --- Client Email Login API ---
class ClientEmailLoginRequest(APIView):
    def post(self, request):
        identifier = request.data.get('identifier')  # username or email
        if not identifier:
            return Response({'success': False, 'error': 'Identifier required.'}, status=400)
        User = get_user_model()
        try:
            user = User.objects.get((Q(username=identifier) | Q(email=identifier)), is_client=True, is_active=True)
        except User.DoesNotExist:
            return Response({'success': False, 'error': 'No active client user found.'}, status=404)
        # Generate time-limited token (30 min)
        timed_serializer = URLSafeTimedSerializer(SECRET)
        token = timed_serializer.dumps({'user_id': user.id})
        login_url = request.build_absolute_uri(reverse('client_email_login_verify', args=[token]))
        send_mail(
            'Your Secure Login Link',
            'Click the link to log in.',
            'admin@test.com',
            [user.email],
        )
        return Response({'success': True, 'message': 'Login link sent to your email.'})

# --- Secure Email Login for Ops and Client ---
@csrf_exempt
def ops_login_view(request):
    if request.user.is_authenticated and hasattr(request.user, 'is_ops') and request.user.is_ops:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if hasattr(user, 'is_ops') and user.is_ops:
                # Send secure login link to ops email
                timed_serializer = URLSafeTimedSerializer(SECRET)
                token = timed_serializer.dumps({'user_id': user.id, 'role': 'ops'})
                # login_url = request.build_absolute_uri(reverse('ops_email_login_verify', args=[token]))
                # login_url = login_url.replace(request.get_host(), '127.0.0.1:8000')
                send_mail(
                    'Your Secure Ops Login Link',
                    'Click the link to log in.',
                    'admin@test.com',
                    [user.email],
                )
                messages.success(request, 'A secure login link has been sent to your email.')
                return render(request, 'api/login.html', {'form': form, 'ops_login': True, 'email_sent': True})
            else:
                messages.error(request, 'You are not authorized as an Ops user.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'api/login.html', {'form': form, 'ops_login': True})

@csrf_exempt
def client_login_view(request):
    if request.user.is_authenticated and hasattr(request.user, 'is_client') and request.user.is_client:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if hasattr(user, 'is_client') and user.is_client:
                # Send secure login link to client email
                timed_serializer = URLSafeTimedSerializer(SECRET)
                token = timed_serializer.dumps({'user_id': user.id, 'role': 'client'})
                # login_url = request.build_absolute_uri(reverse('client_email_login_verify', args=[token]))
                # login_url = login_url.replace(request.get_host(), '127.0.0.1:8000')
                send_mail(
                    'Your Secure Client Login Link',
                    'Click the link to log in.',
                    'admin@test.com',
                    [user.email],
                )
                messages.success(request, 'A secure login link has been sent to your email.')
                return render(request, 'api/login.html', {'form': form, 'client_login': True, 'email_sent': True})
            else:
                messages.error(request, 'You are not authorized as a Client user.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'api/login.html', {'form': form, 'client_login': True})

# --- Secure Email Login Verification for Ops ---
class OpsEmailLoginVerify(APIView):
    def get(self, request, token):
        timed_serializer = URLSafeTimedSerializer(SECRET)
        try:
            data = timed_serializer.loads(token, max_age=1800)  # 30 min expiry
            user_id = data['user_id']
            role = data.get('role')
            User = get_user_model()
            user = User.objects.get(id=user_id, is_ops=True, is_active=True)
            login(request, user)
            return redirect('dashboard')
        except SignatureExpired:
            return JsonResponse({'success': False, 'error': 'Token expired.'}, status=400)
        except BadSignature:
            return JsonResponse({'success': False, 'error': 'Invalid token.'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid token.'}, status=400)

# --- Secure Email Login Verification for Client ---
class ClientEmailLoginVerify(APIView):
    def get(self, request, token):
        timed_serializer = URLSafeTimedSerializer(SECRET)
        try:
            data = timed_serializer.loads(token, max_age=1800)  # 30 min expiry
            user_id = data['user_id']
            role = data.get('role')
            User = get_user_model()
            user = User.objects.get(id=user_id, is_client=True, is_active=True)
            login(request, user)
            return redirect('home')
        except SignatureExpired:
            return JsonResponse({'success': False, 'error': 'Token expired.'}, status=400)
        except BadSignature:
            return JsonResponse({'success': False, 'error': 'Invalid token.'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid token.'}, status=400)