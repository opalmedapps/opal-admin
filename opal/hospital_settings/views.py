"""This module provides views for hospital-specific settings."""
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from .models import Institution, Site


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
