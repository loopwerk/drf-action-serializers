from rest_framework import mixins as rest_mixins
from rest_framework import viewsets

from . import mixins
from .generics import ActionSerializerGenericAPIView


class ActionSerializerGenericViewSet(viewsets.ViewSetMixin, ActionSerializerGenericAPIView):
    pass


class ActionSerializerReadOnlyModelViewSet(
    rest_mixins.RetrieveModelMixin, rest_mixins.ListModelMixin, ActionSerializerGenericViewSet
):
    pass


class ActionSerializerModelViewSet(
    mixins.ActionSerializerCreateModelMixin,
    rest_mixins.RetrieveModelMixin,
    mixins.ActionSerializerUpdateModelMixin,
    rest_mixins.DestroyModelMixin,
    rest_mixins.ListModelMixin,
    ActionSerializerGenericViewSet,
):
    pass
