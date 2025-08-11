# accounts/serializers.py

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = self.initial_data
        # If client sent "email" only, map it to the username field SimpleJWT expects
        if 'email' in data and 'username' not in data:
            try:
                user = User.objects.get(email=data['email'])
                attrs[User.USERNAME_FIELD] = getattr(user, User.USERNAME_FIELD)
            except User.DoesNotExist:
                pass
        return super().validate(attrs)
