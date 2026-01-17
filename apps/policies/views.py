from rest_framework import viewsets
from .models import MaintenancePolicy
from django.http import HttpResponse
from .pdf import generate_policy_pdf
from .serializers import MaintenancePolicySerializer

def download_policy_pdf(request, pk):
    policy = MaintenancePolicy.objects.get(pk=pk)
    buffer = generate_policy_pdf(policy)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="policy_{policy.pk}.pdf"'
    return response

class MaintenancePolicyViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePolicy.objects.all()
    serializer_class = MaintenancePolicySerializer


