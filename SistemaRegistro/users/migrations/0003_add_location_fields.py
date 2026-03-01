# Generated migration for adding location fields to UserProfile

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_add_superuser_type'),
        ('registry', '0011_sistema_institucional'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='estado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='registry.estado'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='municipio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='registry.municipio'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='parroquia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='registry.parroquia'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='ubicacion',
            field=models.TextField(blank=True),
        ),
    ]
