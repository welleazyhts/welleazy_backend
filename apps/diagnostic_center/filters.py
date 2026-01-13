import django_filters
from apps.diagnostic_center.models import DiagnosticCenter
from apps.health_packages.models import HealthPackage
from apps.sponsored_packages.models import SponsoredPackage
from apps.labtest.models import Test

class DiagnosticCenterFilter(django_filters.FilterSet):
    city_id = django_filters.NumberFilter(field_name='city__id', required=True)
    tests = django_filters.ModelMultipleChoiceFilter(
        queryset=Test.objects.all(),
        method='filter_tests_conjoined'
    )

    def filter_tests_conjoined(self, queryset, name, value):
        if not value:
            return queryset
        
        # To get centers that have ALL requested tests, we chain filter() calls
        for test in value:
            queryset = queryset.filter(tests=test)
        return queryset.distinct()
    health_package_id = django_filters.ModelChoiceFilter(
        queryset=HealthPackage.objects.all(),
        field_name='health_packages'
    )
    sponsored_package_id = django_filters.ModelChoiceFilter(
        queryset=SponsoredPackage.objects.all(),
        field_name='sponsored_packages'
    )

    class Meta:
        model = DiagnosticCenter
        fields = ['city_id', 'tests', 'health_package_id', 'sponsored_package_id']
