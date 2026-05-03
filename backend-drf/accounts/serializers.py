from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'}) 
    # password should only be set , it should not be retrived that why we wrote write_only=True it should only work with post method , he cannot be able to get the password through get request.
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        #  this means serializers will automatically validate the data that we have entered in  the form 
        # User.objects.create = save the password in a plain text
        # User.objects.create_user = automatically hash the password
        user = User.objects.create_user(
            validated_data['username'],
            validated_data['email'],
            validated_data['password']
        )
        # user = User.objects.create_user(**validated_data)
        # we use this method when we have only 3 required fields 
        # username , email and password then we use this method directly
        # instead of create_user above method 
        return user