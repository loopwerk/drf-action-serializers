from rest_framework import mixins, status
from rest_framework.response import Response


class ActionSerializerCreateModelMixin(mixins.CreateModelMixin):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = self.get_action_serializer("read")(
            instance=serializer.instance,
            context=self.get_serializer_context(),
        )

        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ActionSerializerUpdateModelMixin(mixins.UpdateModelMixin):
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        response_serializer = self.get_action_serializer("read")(
            instance=serializer.instance,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data)
