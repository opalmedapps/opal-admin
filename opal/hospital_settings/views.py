from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from rest_framework import permissions, viewsets

from .models import Institution, Site
from .serializers import InstitutionSerializer, SiteSerializer


# REST API
class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['code']


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # see: https://github.com/carltongibson/django-filter/issues/1076#issuecomment-489252242
    filterset_fields = {
        'code': ['in'],
        'institution__code': ['exact'],
    }


# Web pages
class HomePageView(TemplateView):
    template_name = 'hospital_settings/index.html'


# INSTITUTIONS
class InstitutionListView(ListView):
    model = Institution
    template_name = 'hospital_settings/institution/institution_list.html'


class InstitutionCreateView(CreateView):
    model = Institution
    template_name = 'hospital_settings/institution/institution_form.html'
    fields = ['name_en', 'name_fr', 'code']
    success_url = reverse_lazy('institution-list')


class InstitutionDetailView(DetailView):
    model = Institution
    template_name = 'hospital_settings/institution/institution_detail.html'


class InstitutionUpdateView(UpdateView):
    model = Institution
    template_name = 'hospital_settings/institution/institution_form.html'
    fields = fields = ['name_en', 'name_fr', 'code']
    success_url = reverse_lazy('institution-list')


class InstitutionDeleteView(DeleteView):
    model = Institution
    success_url = reverse_lazy('institution-list')


# SITES
class SiteListView(ListView):
    model = Site
    template_name = 'hospital_settings/site/site_list.html'


class SiteCreateView(CreateView):
    model = Site
    template_name = 'hospital_settings/site/site_form.html'
    fields = ['name_en', 'name_fr', 'parking_url_en', 'parking_url_fr', 'code', 'institution']
    success_url = reverse_lazy('site-list')


class SiteDetailView(DetailView):
    model = Site
    template_name = 'hospital_settings/site/site_detail.html'


class SiteUpdateView(UpdateView):
    model = Site
    template_name = 'hospital_settings/site/site_form.html'
    fields = ['name_en', 'name_fr', 'parking_url_en', 'parking_url_fr', 'code', 'institution']
    success_url = reverse_lazy('site-list')


class SiteDeleteView(DeleteView):
    model = Site
    success_url = reverse_lazy('site-list')
