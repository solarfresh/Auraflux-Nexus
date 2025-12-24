from uuid import UUID

from .models import TopicKeyword, TopicScopeElement


def update_topic_scope_element_by_id(scope_id: UUID, scope_label: str, scope_rationale: str, scope_status: str | None = None, serializer_class = None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    scope_instance = TopicScopeElement.objects.get(id=scope_id)

    scope_instance.label = scope_label
    scope_instance.rationale = scope_rationale
    if scope_status is not None:
        scope_instance.status = scope_status

    scope_instance.save()

    instances = TopicScopeElement.objects.filter(object_id=scope_instance.object_id).all()
    serializer = serializer_class(instances, many=True)
    return serializer.data

def update_topic_keyword_by_id(keyword_id: UUID, keyword_label: str, keyword_status: str | None = None, serializer_class = None):
    if serializer_class is None:
        raise ValueError("serializer_class must be provided")

    keyword_instance = TopicKeyword.objects.get(id=keyword_id)

    keyword_instance.label = keyword_label
    if keyword_status is not None:
        keyword_instance.status = keyword_status

    keyword_instance.save()

    instances = TopicKeyword.objects.filter(object_id=keyword_instance.object_id).all()
    serializer = serializer_class(instances, many=True)
    return serializer.data
