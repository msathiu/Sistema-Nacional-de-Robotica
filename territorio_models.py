from django.db import models

class Estados(models.Model):
    id_estado = models.IntegerField(primary_key=True)
    estado = models.CharField(max_length=100)
    iso_3166_2 = models.CharField(max_length=4)

    class Meta:
        managed = False
        db_table = 'estados'

class Municipios(models.Model):
    id_municipio = models.IntegerField(primary_key=True)
    id_estado = models.ForeignKey(Estados, models.DO_NOTHING, db_column='id_estado')
    municipio = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'municipios'