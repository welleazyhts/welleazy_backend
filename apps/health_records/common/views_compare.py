from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.apps import apps

from .compare_engine import filter_record_for_compare, get_model_from_module, dict_diff

from django.apps import apps as django_apps

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def compare_records(request):
    module = request.data.get("module")
    record_ids = request.data.get("record_ids")

    if not module:
        raise ValidationError({"module": "module is required"})
    if not record_ids or not isinstance(record_ids, list):
        raise ValidationError({"record_ids": "record_ids must be a list"})

    # Get the model from YOUR mapping
    Model = get_model_from_module(module)

    # Fetch records
    qs = Model.objects.filter(id__in=record_ids)
    if hasattr(Model, "deleted_at"):
        qs = qs.filter(deleted_at__isnull=True)

    records = list(qs)
    if len(records) != len(record_ids):
        raise ValidationError("Some record_ids are invalid")

    app_config = django_apps.get_app_config(Model._meta.app_label)
    serializer_module_path = app_config.name + ".serializers" 
    serializer_class_name = Model.__name__ + "Serializer"       

    serializers_module = __import__(serializer_module_path, fromlist=[serializer_class_name])
    serializer_class = getattr(serializers_module, serializer_class_name)

    # Serialize with context
    raw = serializer_class(records, many=True, context={"request": request}).data

    # Filter before diff
    filtered = [filter_record_for_compare(item) for item in raw]

    differences = dict_diff(filtered)

    return Response({
        "module": module,
        "records": filtered,
        "differences": differences,
    })

