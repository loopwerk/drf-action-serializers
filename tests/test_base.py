import pytest
from rest_framework import serializers, status
from rest_framework.test import APIRequestFactory

from drf_action_serializer.viewsets import ActionSerializerModelViewSet
from tests.models import Thing


class WriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thing
        fields = ["id", "name"]


class ReadSerializer(serializers.ModelSerializer):
    extra = serializers.SerializerMethodField()

    class Meta:
        model = Thing
        fields = ["id", "name", "extra"]

    def get_extra(self, obj):
        return "extra value"


class ViewSet(ActionSerializerModelViewSet):
    serializer_class = WriteSerializer
    read_serializer_class = ReadSerializer
    queryset = Thing.objects.all()


@pytest.fixture
def viewset():
    return ViewSet.as_view({"post": "create", "patch": "partial_update"})


@pytest.mark.django_db
def test_create_uses_read_serializer(viewset):
    factory = APIRequestFactory()
    request = factory.post("/", {"name": "new"}, format="json")
    response = viewset(request)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "new"
    assert response.data["extra"] == "extra value"


@pytest.mark.django_db
def test_partial_update_uses_read_serializer(viewset):
    thing = Thing.objects.create(name="existing")

    factory = APIRequestFactory()
    request = factory.patch("/", {"name": "patched"}, format="json")
    response = viewset(request, pk=thing.pk)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "patched"
    assert response.data["extra"] == "extra value"
