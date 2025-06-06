from drf_spectacular.openapi import AutoSchema


class ActionSerializerAutoSchema(AutoSchema):
    def get_request_serializer(self):
        if self.method.lower() in {"post", "put", "patch"}:
            if hasattr(self.view, "get_action_serializer"):
                return self.view.get_action_serializer("write")
        return super().get_request_serializer()

    def get_response_serializers(self):
        if not hasattr(self.view, "get_action_serializer"):
            return super().get_response_serializers()

        method = self.method.lower()

        if method == "post":
            return {
                "201": self.view.get_action_serializer("read"),
            }
        elif method in {"put", "patch"}:
            return {
                "200": self.view.get_action_serializer("read"),
            }

        return super().get_response_serializers()
