import pytest

drf_spectacular = pytest.importorskip("drf_spectacular")

from rest_framework import serializers

from drf_action_serializer.spectacular import ActionSerializerAutoSchema


class ReadSerializer(serializers.Serializer):
    name = serializers.CharField()
    read_only = serializers.CharField()


class WriteSerializer(serializers.Serializer):
    name = serializers.CharField()


class FakeView:
    def get_action_serializer(self, method: str):
        return {"read": ReadSerializer, "write": WriteSerializer}[method]

    def __init__(self, method):
        self.request = type("Request", (), {"method": method.upper()})()


def test_post_response_and_request_schema():
    schema = ActionSerializerAutoSchema()
    schema.method = "post"
    schema.view = FakeView("POST")

    # Test request serializer
    request_serializer = schema.get_request_serializer()
    assert request_serializer is WriteSerializer

    # Test response serializer
    response_serializers = schema.get_response_serializers()
    assert response_serializers == {"201": ReadSerializer}


def test_patch_response_and_request_schema():
    schema = ActionSerializerAutoSchema()
    schema.method = "patch"
    schema.view = FakeView("PATCH")

    assert schema.get_request_serializer() is WriteSerializer
    assert schema.get_response_serializers() == {"200": ReadSerializer}
