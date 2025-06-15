from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, Problem, Department

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'department', 'role']
        extra_kwargs = {
            'id': {'read_only': True},
            'password': {'write_only': True}
        }

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    department = serializers.SlugRelatedField(
        slug_field='id',               # Use string id now
        queryset=Department.objects.all()
    )

    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'role', 'department']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            name=validated_data['name'],
            role=validated_data['role'],
            department=validated_data['department']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = '__all__'
