# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0031_participante_nacionalidad_representante'),
    ]

    operations = [
        migrations.AddField(
            model_name='evento',
            name='telefono_codigo',
            field=models.CharField(blank=True, choices=[('0424', '0424'), ('0414', '0414'), ('0422', '0422'), ('0412', '0412'), ('0426', '0426'), ('0416', '0416')], help_text='Código de área del teléfono de contacto', max_length=4, verbose_name='Código de Área'),
        ),
        migrations.AddField(
            model_name='evento',
            name='telefono_numero',
            field=models.CharField(blank=True, help_text='Número de teléfono de contacto (7 dígitos)', max_length=7, verbose_name='Número de Teléfono'),
        ),
        migrations.AddField(
            model_name='evento',
            name='email_contacto',
            field=models.EmailField(blank=True, help_text='Correo electrónico de contacto del evento', max_length=254, verbose_name='Correo de Contacto'),
        ),
    ]
