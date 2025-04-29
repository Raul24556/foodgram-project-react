from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer as DJSetPasswordSerializer
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from users.models import Follow
from users.serializers import (AvatarSerializer, CreateUsrrSerializer,
                               FollowSerializer, UserListSerializer,
                               UserSubscribesSerializer)

User = get_user_model()


class UserViewSet(ModelViewSet):
    """Вьюсет пользователей."""

    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "set_password":
            return DJSetPasswordSerializer
        elif self.action == 'create':
            return CreateUsrrSerializer
        elif self.action == 'avatar':
            return AvatarSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action == "retrieve":
            self.permission_classes = [AllowAny]
        elif self.action == 'list':
            self.permission_classes = [AllowAny]
        elif self.action == 'create':
            self.permission_classes = [AllowAny]
        elif self.action == "me":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(["get", ], detail=False)
    def me(self, request):
        user = self.request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(["put", 'delete'],
            detail=False,
            url_path='me/avatar',
            url_name='me-avatar')
    def avatar(self, request):
        image = self.request.data
        if self.request.method == "DELETE":
            image = {'avatar': None}
        instance = self.request.user
        serializer = self.get_serializer(instance, data=image, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if self.request.method == "DELETE":
            return Response(status=status.HTTP_204_NO_CONTENT)
        if 'avatar' not in self.request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)

    @action(["post"], detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    """Вью сет подписчиков."""

    permission_classes = [AllowAny]
    serializer_class = UserSubscribesSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class UserSubscribeView(APIView):
    """Создание или удаление подписки на пользователя."""

    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        serializer = FollowSerializer(
            data={'user': request.user.id, 'following': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED
                        )

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        if not Follow.objects.filter(
            user=request.user,
            following=author
        ).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Follow.objects.get(
            user=request.user.id,
            following=user_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
