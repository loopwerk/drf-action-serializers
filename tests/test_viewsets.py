import pytest
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from drf_action_serializers.viewsets import ActionSerializerModelViewSet
from tests.models import Thing


class WriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thing
        fields = ["id", "name"]


class RetrieveSerializer(serializers.ModelSerializer):
    extra = serializers.SerializerMethodField()

    class Meta:
        model = Thing
        fields = ["id", "name", "extra"]

    def get_extra(self, obj):
        return "extra value"


class ListSerializer(serializers.ModelSerializer):
    """Simple serializer for list view with minimal fields"""

    class Meta:
        model = Thing
        fields = ["id", "name"]


class ThingCustomActionSerializer(serializers.ModelSerializer):
    """Serializer for custom action"""

    name_uppercase = serializers.SerializerMethodField()

    class Meta:
        model = Thing
        fields = ["id", "name", "name_uppercase"]

    def get_name_uppercase(self, obj):
        return obj.name.upper()


class TestPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100


class BasicViewSet(ActionSerializerModelViewSet):
    """ViewSet using different serializers for write and read methods"""

    write_serializer_class = WriteSerializer
    serializer_class = RetrieveSerializer
    queryset = Thing.objects.all()


class AdvancedViewSet(ActionSerializerModelViewSet):
    """ViewSet using different serializers for list and retrieve actions"""

    queryset = Thing.objects.all().order_by("id")
    list_serializer_class = ListSerializer
    retrieve_serializer_class = RetrieveSerializer
    write_serializer_class = WriteSerializer
    create_read_serializer_class = ListSerializer
    update_read_serializer_class = RetrieveSerializer
    pagination_class = TestPagination

    @action(detail=True, methods=["get"])
    def uppercase(self, request, pk=None):
        thing = self.get_object()
        serializer = self.get_serializer(thing)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action == "uppercase":
            return ThingCustomActionSerializer
        return super().get_serializer_class()


class FallbackViewSet(ActionSerializerModelViewSet):
    """ViewSet to test all serializer fallback paths"""

    queryset = Thing.objects.all()
    serializer_class = WriteSerializer  # Final fallback
    read_serializer_class = RetrieveSerializer  # Method fallback
    create_read_serializer_class = ListSerializer  # Action-specific read
    update_read_serializer_class = RetrieveSerializer  # Action-specific read
    update_serializer_class = WriteSerializer  # Action fallback


class NoSerializerViewSet(ActionSerializerModelViewSet):
    queryset = Thing.objects.all()
    # No serializer_class or any action-specific serializers


# Fixtures
@pytest.fixture
def basic_viewset():
    return BasicViewSet.as_view({"post": "create", "patch": "partial_update"})


@pytest.fixture
def advanced_viewset():
    return AdvancedViewSet.as_view({"get": "list", "post": "create"})


@pytest.fixture
def advanced_detail_viewset():
    return AdvancedViewSet.as_view({"get": "retrieve", "patch": "partial_update"})


@pytest.fixture
def custom_action_viewset():
    return AdvancedViewSet.as_view({"get": "uppercase"})


@pytest.fixture
def fallback_viewset():
    return FallbackViewSet.as_view({"get": "list", "post": "create", "patch": "partial_update"})


@pytest.fixture
def no_serializer_viewset():
    return NoSerializerViewSet.as_view({"get": "list", "post": "create"})


# Basic read/write tests
@pytest.mark.django_db
def test_create_uses_read_serializer(basic_viewset):
    factory = APIRequestFactory()
    request = factory.post("/", {"name": "new"}, format="json")
    response = basic_viewset(request)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "new"
    assert response.data["extra"] == "extra value"


@pytest.mark.django_db
def test_partial_update_uses_read_serializer(basic_viewset):
    thing = Thing.objects.create(name="existing")

    factory = APIRequestFactory()
    request = factory.patch("/", {"name": "patched"}, format="json")
    response = basic_viewset(request, pk=thing.pk)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "patched"
    assert response.data["extra"] == "extra value"


# Advanced action-specific tests
@pytest.mark.django_db
def test_list_action_uses_list_serializer(advanced_viewset):
    # Create some test data
    Thing.objects.create(name="short")
    Thing.objects.create(name="very long name")

    factory = APIRequestFactory()
    request = factory.get("/")
    response = advanced_viewset(request)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2

    # Verify list serializer fields
    first_item = response.data[0]
    assert "id" in first_item
    assert "name" in first_item
    assert "extra" not in first_item


@pytest.mark.django_db
def test_retrieve_action_uses_detail_serializer(advanced_detail_viewset):
    # Create test data
    thing = Thing.objects.create(name="very long name")

    factory = APIRequestFactory()
    request = factory.get("/")
    response = advanced_detail_viewset(request, pk=thing.pk)

    assert response.status_code == status.HTTP_200_OK

    # Verify detail serializer fields
    assert response.data["id"] == thing.id
    assert response.data["name"] == "very long name"
    assert response.data["extra"] == "extra value"


@pytest.mark.django_db
def test_create_uses_write_serializer(advanced_viewset):
    factory = APIRequestFactory()

    # Test valid creation
    request = factory.post("/", {"name": "valid name"}, format="json")
    response = advanced_viewset(request)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "valid name"


@pytest.mark.django_db
def test_update_uses_write_serializer(advanced_detail_viewset):
    thing = Thing.objects.create(name="original name")
    factory = APIRequestFactory()

    # Test valid update
    request = factory.patch("/", {"name": "new valid name"}, format="json")
    response = advanced_detail_viewset(request, pk=thing.pk)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "new valid name"


@pytest.mark.django_db
def test_custom_action_uses_custom_serializer(custom_action_viewset):
    thing = Thing.objects.create(name="test name")
    factory = APIRequestFactory()

    request = factory.get("/")
    response = custom_action_viewset(request, pk=thing.pk)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "test name"
    assert response.data["name_uppercase"] == "TEST NAME"


@pytest.mark.django_db
def test_list_pagination(advanced_viewset):
    # Create multiple items
    for i in range(15):
        Thing.objects.create(name=f"item {i}")

    factory = APIRequestFactory()
    request = factory.get("/?page=2&page_size=5")
    response = advanced_viewset(request)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 5
    assert "count" in response.data
    assert "next" in response.data
    assert "previous" in response.data


@pytest.mark.django_db
def test_serializer_fallback_paths(fallback_viewset):
    factory = APIRequestFactory()

    # Test create action with action-specific read serializer
    request = factory.post("/", {"name": "new"}, format="json")
    response = fallback_viewset(request)
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.data
    assert "name" in response.data
    assert "extra" not in response.data  # ListSerializer doesn't have extra field

    # Test partial_update action with update-specific read serializer
    thing = Thing.objects.create(name="existing")
    request = factory.patch("/", {"name": "patched"}, format="json")
    response = fallback_viewset(request, pk=thing.pk)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "patched"
    assert response.data["extra"] == "extra value"  # RetrieveSerializer has extra field

    # Test list action with method fallback
    request = factory.get("/")
    response = fallback_viewset(request)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) > 0
    assert "id" in response.data[0]
    assert "name" in response.data[0]
    assert "extra" in response.data[0]  # read_serializer_class (RetrieveSerializer) is used


class MinimalViewSet(ActionSerializerModelViewSet):
    """ViewSet with minimal serializer configuration"""

    queryset = Thing.objects.all()
    serializer_class = WriteSerializer  # Only final fallback


@pytest.fixture
def minimal_viewset():
    return MinimalViewSet.as_view({"get": "list", "post": "create", "patch": "partial_update"})


@pytest.mark.django_db
def test_minimal_serializer_configuration(minimal_viewset):
    factory = APIRequestFactory()

    # Test that all actions fall back to serializer_class
    # Create
    request = factory.post("/", {"name": "new"}, format="json")
    response = minimal_viewset(request)
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.data
    assert "name" in response.data
    assert "extra" not in response.data

    # Update
    thing = Thing.objects.create(name="existing")
    request = factory.patch("/", {"name": "patched"}, format="json")
    response = minimal_viewset(request, pk=thing.pk)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "patched"
    assert "extra" not in response.data

    # List
    request = factory.get("/")
    response = minimal_viewset(request)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) > 0
    assert "id" in response.data[0]
    assert "name" in response.data[0]
    assert "extra" not in response.data[0]


@pytest.mark.django_db
def test_error_when_no_serializer_found(no_serializer_viewset):
    factory = APIRequestFactory()
    # Test GET (list)
    request = factory.get("/")
    with pytest.raises(AssertionError) as excinfo:
        no_serializer_viewset(request)
    assert "must define a suitable serializer" in str(excinfo.value)

    # Test POST (create)
    request = factory.post("/", {"name": "test"}, format="json")
    with pytest.raises(AssertionError) as excinfo:
        no_serializer_viewset(request)
    assert "must define a suitable serializer" in str(excinfo.value)
