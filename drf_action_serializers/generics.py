from rest_framework import permissions
from rest_framework.generics import GenericAPIView


class ActionSerializerGenericAPIView(GenericAPIView):
    def get_action_serializer(self, method):
        assert hasattr(self, "action"), "View must have an `action` attribute"

        candidates = [
            f"{self.action}_{method}_serializer_class",
            f"{method}_serializer_class",
            f"{self.action}_read_serializer_class",
            f"{self.action}_serializer_class",
        ]

        # Fallback to update if action is partial_update and no exact match found
        if self.action == "partial_update":
            candidates += [
                f"update_{method}_serializer_class",
                "update_read_serializer_class",
                "update_serializer_class",
            ]

        candidates += [
            "read_serializer_class",
            "serializer_class",
        ]

        for attr in candidates:
            result = getattr(self, attr, None)
            if result is not None:
                return result

        raise AssertionError(
            f"{self.__class__.__name__} must define a suitable serializer. Tried: {', '.join(candidates)}"
        )

    def get_serializer_class(self):
        method = "read" if self.request.method in permissions.SAFE_METHODS else "write"
        return self.get_action_serializer(method)
