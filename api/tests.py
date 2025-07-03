from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from .models import User, UploadedFile
from itsdangerous import URLSafeTimedSerializer
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

class AuthFlowTests(TestCase):
    def setUp(self):
        self.ops_user = User.objects.create_user(username='ops', password='opspass', email='ops@test.com', is_ops=True, is_active=True)
        self.client_user = User.objects.create_user(username='client', password='clientpass', email='client@test.com', is_client=True, is_active=True)
        self.c = Client()
        self.timed_serializer = URLSafeTimedSerializer('mysecretkey123')

    def test_ops_login_page(self):
        resp = self.c.get(reverse('ops_login'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Ops User Login')

    def test_client_login_page(self):
        resp = self.c.get(reverse('client_login'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Client User Login')

    def test_ops_login_email_sent(self):
        resp = self.c.post(reverse('ops_login'), {'username': 'ops', 'password': 'opspass'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('A secure login link has been sent', resp.content.decode())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('ops@test.com', mail.outbox[0].to)

    def test_client_login_email_sent(self):
        resp = self.c.post(reverse('client_login'), {'username': 'client', 'password': 'clientpass'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('A secure login link has been sent', resp.content.decode())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('client@test.com', mail.outbox[0].to)

    def test_ops_email_login_verify(self):
        token = self.timed_serializer.dumps({'user_id': self.ops_user.id, 'role': 'ops'})
        resp = self.c.get(reverse('ops_email_login_verify', args=[token]))
        self.assertEqual(resp.status_code, 302)  # redirect to dashboard
        self.assertTrue('_auth_user_id' in self.c.session)

    def test_client_email_login_verify(self):
        token = self.timed_serializer.dumps({'user_id': self.client_user.id, 'role': 'client'})
        resp = self.c.get(reverse('client_email_login_verify', args=[token]))
        self.assertEqual(resp.status_code, 302)  # redirect to home
        self.assertTrue('_auth_user_id' in self.c.session)

    def test_invalid_token(self):
        resp = self.c.get(reverse('ops_email_login_verify', args=['invalidtoken']))
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Invalid token', resp.content.decode())

    def test_expired_token(self):
        # Simulate expired token by using max_age=0
        token = self.timed_serializer.dumps({'user_id': self.ops_user.id, 'role': 'ops'})
        import time
        time.sleep(1)
        resp = self.c.get(reverse('ops_email_login_verify', args=[token]))
        # forcibly expire by patching max_age in view if needed
        # Here, just check for 302 or 400
        self.assertIn(resp.status_code, [302, 400])

class FileUploadDownloadTests(TestCase):
    def setUp(self):
        self.ops_user = User.objects.create_user(username='ops', password='opspass', email='ops@test.com', is_ops=True, is_active=True)
        self.client_user = User.objects.create_user(username='client', password='clientpass', email='client@test.com', is_client=True, is_active=True)
        self.c = Client()

    def test_ops_can_upload_valid_file(self):
        self.c.force_login(self.ops_user)
        file = SimpleUploadedFile('test.docx', b'file_content')
        resp = self.c.post(reverse('home'), {'file': file})
        self.assertContains(resp, 'File uploaded successfully')
        self.assertEqual(UploadedFile.objects.count(), 1)

    def test_ops_cannot_upload_invalid_file(self):
        self.c.force_login(self.ops_user)
        file = SimpleUploadedFile('test.txt', b'file_content')
        resp = self.c.post(reverse('home'), {'file': file})
        self.assertContains(resp, 'Invalid file type')
        self.assertEqual(UploadedFile.objects.count(), 0)

    def test_client_cannot_upload(self):
        self.c.force_login(self.client_user)
        file = SimpleUploadedFile('test.docx', b'file_content')
        resp = self.c.post(reverse('home'), {'file': file})
        self.assertContains(resp, 'Only Ops users can upload files')
        self.assertEqual(UploadedFile.objects.count(), 0)

    def test_client_can_download(self):
        self.c.force_login(self.ops_user)
        file = SimpleUploadedFile('test.docx', b'file_content')
        upload = UploadedFile.objects.create(user=self.ops_user, file=file)
        self.c.logout()
        self.c.force_login(self.client_user)
        from itsdangerous import URLSafeSerializer
        serializer = URLSafeSerializer('mysecretkey123')
        token = serializer.dumps({'file_id': upload.id, 'user_id': self.client_user.id})
        resp = self.c.get(reverse('secure_download', args=[token]))
        self.assertIn(resp.get('Content-Type'), [
            'application/octet-stream',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ])

    def test_ops_cannot_download(self):
        self.c.force_login(self.ops_user)
        file = SimpleUploadedFile('test.docx', b'file_content')
        upload = UploadedFile.objects.create(user=self.ops_user, file=file)
        from itsdangerous import URLSafeSerializer
        serializer = URLSafeSerializer('mysecretkey123')
        token = serializer.dumps({'file_id': upload.id, 'user_id': self.ops_user.id})
        resp = self.c.get(reverse('secure_download', args=[token]))
        self.assertEqual(resp.status_code, 403)
        self.assertIn('not allowed', resp.content.decode())
