# Generated by Django 4.1.13 on 2024-02-09 19:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Create pharmacy models."""

    initial = True

    dependencies = [
        ('patients', '0025_add_lab_result_delay_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='CodedElement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=50)),
                ('text', models.CharField(max_length=150)),
                ('coding_system', models.CharField(max_length=50)),
                ('alternate_identifier', models.CharField(blank=True, max_length=50)),
                ('alternate_text', models.CharField(blank=True, max_length=150)),
                ('alternate_coding_system', models.CharField(blank=True, max_length=50)),
            ],
            options={
                'verbose_name': 'Coded Element',
                'verbose_name_plural': 'Coded Elements',
                'unique_together': {('identifier', 'coding_system')},
            },
        ),
        migrations.CreateModel(
            name='PharmacyEncodedOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=3, max_digits=8)),
                ('unit', models.CharField(blank=True, max_length=20)),
                ('interval', models.CharField(max_length=100)),
                ('duration', models.CharField(default='INDEF', max_length=50)),
                ('service_start', models.DateTimeField(blank=True)),
                ('service_end', models.DateTimeField(blank=True)),
                ('priority', models.CharField(default='R', max_length=8)),
                ('give_amount_maximum', models.DecimalField(blank=True, decimal_places=3, max_digits=8, null=True)),
                ('give_amount_minimum', models.DecimalField(decimal_places=3, max_digits=8)),
                ('dispense_amount', models.DecimalField(decimal_places=3, max_digits=8)),
                ('refills', models.IntegerField(default=0)),
                ('refills_remaining', models.IntegerField(default=0)),
                ('last_refilled', models.DateTimeField(blank=True)),
                ('formulary_status', models.CharField(choices=[('STD', 'Standard'), ('AMB', 'Ambulatory'), ('LOA', 'Leave Of Absence'), ('TH', 'Take Home'), ('SELF', 'Self Administration')], max_length=4)),
                ('dispense_units', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pharmacy_encoded_order_dispense_units', to='pharmacy.codedelement')),
                ('give_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pharmacy_encoded_order_give_codes', to='pharmacy.codedelement')),
                ('give_dosage_form', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pharmacy_encoded_order_give_dosage_forms', to='pharmacy.codedelement')),
                ('give_units', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pharmacy_encoded_order_give_units', to='pharmacy.codedelement')),
            ],
            options={
                'verbose_name': 'Pharmacy Encoding',
                'verbose_name_plural': 'Pharmacy Encodings',
            },
        ),
        migrations.CreateModel(
            name='PhysicianPrescriptionOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=3, max_digits=8)),
                ('unit', models.CharField(blank=True, max_length=20)),
                ('interval', models.CharField(max_length=100)),
                ('duration', models.CharField(default='INDEF', max_length=50)),
                ('service_start', models.DateTimeField(blank=True)),
                ('service_end', models.DateTimeField(blank=True)),
                ('priority', models.CharField(default='R', max_length=8)),
                ('visit_number', models.IntegerField()),
                ('trigger_event', models.CharField(max_length=2)),
                ('filler_order_number', models.IntegerField()),
                ('order_status', models.CharField(default='SC', max_length=2)),
                ('entered_at', models.DateTimeField()),
                ('entered_by', models.CharField(max_length=80)),
                ('verified_by', models.CharField(max_length=80)),
                ('ordered_by', models.CharField(max_length=80)),
                ('effective_at', models.DateTimeField()),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='physician_prescriptions', to='patients.patient', verbose_name='Patient')),
            ],
            options={
                'verbose_name': 'Physician Prescription',
                'verbose_name_plural': 'Physician Prescriptions',
            },
        ),
        migrations.CreateModel(
            name='PharmacyRoute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('administration_device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pharmacy_route_administration_device', to='pharmacy.codedelement')),
                ('administration_method', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pharmacy_route_administration_method', to='pharmacy.codedelement')),
                ('pharmacy_encoded_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pharmacy.pharmacyencodedorder')),
                ('route', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pharmacy_route_route', to='pharmacy.codedelement')),
                ('site', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pharmacy_route_site', to='pharmacy.codedelement')),
            ],
            options={
                'verbose_name': 'Pharmacy Route',
                'verbose_name_plural': 'Pharmacy Routes',
            },
        ),
        migrations.AddField(
            model_name='pharmacyencodedorder',
            name='physician_prescription_order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pharmacy.physicianprescriptionorder'),
        ),
        migrations.AddField(
            model_name='pharmacyencodedorder',
            name='provider_administration_instruction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pharmacy_encoded_order_provider_administration_instruction', to='pharmacy.codedelement'),
        ),
        migrations.CreateModel(
            name='PharmacyComponent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('component_type', models.CharField(choices=[('A', 'Additive'), ('B', 'Base'), ('T', 'Text')], max_length=1)),
                ('component_amount', models.DecimalField(decimal_places=3, max_digits=8)),
                ('component_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pharmacy_component_component_code', to='pharmacy.codedelement')),
                ('component_units', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pharmacy_component_component_units', to='pharmacy.codedelement')),
                ('pharmacy_encoded_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pharmacy.pharmacyencodedorder')),
            ],
            options={
                'verbose_name': 'Pharmacy Component',
                'verbose_name_plural': 'Pharmacy Components',
            },
        ),
    ]
