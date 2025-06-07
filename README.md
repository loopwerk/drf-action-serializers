# drf-action-serializers

**An easy way to use different serializers for different actions and request methods in Django REST Framework**

Imagine a simple Django REST Framework serializer and view like this:

```python
from rest_framework import serializers
from rest_framework import viewsets
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = "__all__"

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer

    def get_queryset(self):
        return Post.objects.all()
```

The `PostSerializer` class is used for everything: the list of posts, retrieving a single post, the payload when creating or updating a post, and the response when creating or updating a post.

I find that this is often not what I want; for example I often want a simple version of the model to be returned in the list endpoint (`/posts/`), while the full model is returned in the retrieve endpoint (`/posts/{post_id}/`). And I also often want that the _input_ serializer is different from the _output_ serializer, when creating or updating something.

And when you add extra router actions to your ViewSets and you want to use different serializers for them as well? Things are getting complicated and messy real fast.

That’s where drf-action-serializer comes in. Now your view can look like this:

```python
class PostViewSet(ActionSerializerModelViewSet):
    serializer_class = PostDetailSerializer
    list_serializer_class = PostListSerializer
    write_serializer_class = PostWriteSerializer
```

And just like that you’re using a different serializer for the list action, and for the create and update actions.

Or you can get super specific, like this:

```python
class PostViewSet(ActionSerializerModelViewSet):
    list_read_serializer_class = PostListSerializer
    retrieve_read_serializer_class = PostDetailSerializer
    create_write_serializer_class = PostWriteSerializer
    create_read_serializer_class = PostListSerializer
    update_write_serializer_class = PostWriteSerializer
    update_read_serializer_class = PostDetailSerializer
```

Now you’re using different input and output serializers as well!

## Installation and usage

Install the package:

```bash
$ uv add drf-action-serializers
```

And then use its ViewSets like `ActionSerializerModelViewSet`, `ActionSerializerReadOnlyModelViewSet`, and `ActionSerializerGenericViewSet`, instead of Django REST Framework’s built-in ViewSets.

```python
from drf_action_serializers import viewsets

class PostViewSet(ActionSerializerModelViewSet):
    retrieve_serializer_class = PostDetailSerializer
    list_serializer_class = PostListSerializer
    create_write_serializer_class = PostCreateSerializer
    create_read_serializer_class = PostListSerializer
    update_write_serializer_class = PostUpdateSerializer
    update_read_serializer_class = PostListSerializer
```

Note: this package is built on top of Django Rest Framework, so it assumes that Django Rest Framework is installed and added to your project [as documented](https://www.django-rest-framework.org/#installation).

## drf-spectacular support

If you use drf-spectacular, then install the following optional package:

```bash
$ uv add drf-action-serializers[spectacular]
```

Then add the following to `settings.py` and it’s automatically used:

```python
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_action_serializer.spectacular.ActionSerializerAutoSchema",
}
```

## Tests

Unit tests can be run with `uv run pytest`.

## About Feature Requests

This project is feature-complete — it does what I needed it to do, and I’m not actively looking to expand its functionality.

I’m not accepting feature requests via issues. Please understand that asking for new features is essentially asking for free work — not just to build something, but to maintain it over time. And since I don’t personally need those features, I’m unlikely to invest time in them.

If you’d like to add a new feature, you’re welcome to open a pull request. Just know that I’ll evaluate it carefully, because even merged contributions become part of what I maintain. To avoid spending time on a PR that may not be accepted, I recommend starting a discussion first — that way we can talk through the idea and see if it fits.

This approach helps me avoid burnout and keep the project sustainable. Thanks for understanding!

## Credits

Many thanks to [rest-framework-actions](https://github.com/AlexisMunera98/rest-framework-actions) and [drf-rw-serializers](https://github.com/vintasoftware/drf-rw-serializers) for the inspiration.
