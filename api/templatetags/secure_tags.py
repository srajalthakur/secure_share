from django import template
from itsdangerous import URLSafeSerializer
from ..models import UploadedFile
from django.conf import settings

register = template.Library()

SECRET = 'mysecretkey123'  # Use env in production
serializer = URLSafeSerializer(SECRET)

@register.filter
def secure_token(file, user):
    token = serializer.dumps({'file_id': file.id, 'user_id': user.id})
    return token

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
