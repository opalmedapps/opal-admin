from django.contrib.auth.mixins import PermissionRequiredMixin
from django.forms.models import ModelForm
from django.views import generic
from django.urls import reverse_lazy

from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from . import filters, tables
from .models import Caregiver


class EmptyByDefaultFilterView(FilterView):
    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)

        if (
            # not self.filterset.is_bound
            self.filterset.is_valid()
            or not self.get_strict()
        ):
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()

        context = self.get_context_data(
            filter=self.filterset, object_list=self.object_list,
        )
        return self.render_to_response(context)

class CaregiverListView(PermissionRequiredMixin, SingleTableMixin, EmptyByDefaultFilterView):
    model = Caregiver
    permission_required = ('caregivers.view_caregivers',)
    table_class = tables.UserTable
    template_name = 'users/caregivers/list.html'
    queryset = Caregiver.objects.all()
    filterset_class = filters.UserFilter


class UpdateCaregiverView(PermissionRequiredMixin, generic.UpdateView[Caregiver, ModelForm[Caregiver]]):
    model = Caregiver
    permission_required = ('caregivers.edit_caregivers',)
    template_name = 'users/caregivers/edit.html'
    success_url = reverse_lazy('users:caregivers-list')
    fields = ['first_name', 'last_name', 'email', 'phone_number']
