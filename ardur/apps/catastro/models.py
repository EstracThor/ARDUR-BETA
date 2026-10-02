from django.contrib.gis.db import models
from ardur.apps.core.models import Entity

class CatastroVersion(Entity):
    nombre = models.CharField(max_length=255)
    periodo = models.CharField(max_length=7)
    archivo_origen = models.FileField(upload_to='catastro/%Y/%m/')
    sha256 = models.CharField(max_length=64, unique=True)
    fecha_importacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=False)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['activo'], condition=models.Q(activo=True), name='catastro_una_version_activa')]

class Predio(Entity):
    version = models.ForeignKey(CatastroVersion, on_delete=models.PROTECT)
    source_fid = models.CharField(max_length=100)
    provincia = models.CharField(max_length=50, blank=True)
    canton = models.CharField(max_length=50, blank=True)
    parroquia = models.CharField(max_length=100, blank=True, db_index=True)
    zona = models.CharField(max_length=50, blank=True)
    sector = models.CharField(max_length=50, blank=True)
    manzana = models.CharField(max_length=50, blank=True)
    predio = models.CharField(max_length=50, blank=True)
    barrio = models.TextField(blank=True)
    direccion = models.TextField(blank=True)
    clave_ante = models.CharField(max_length=254, blank=True, db_index=True)
    clave_nuev = models.CharField(max_length=254, blank=True, db_index=True)
    predio_mun = models.CharField(max_length=254, blank=True, db_index=True)
    clave_ag = models.CharField(max_length=254, blank=True, db_index=True)
    cod_client = models.CharField(max_length=254, blank=True, db_index=True)
    nombres_catastro = models.TextField(blank=True)
    ruc_cedula_catastro = models.CharField(max_length=254, blank=True, db_index=True)
    suministro = models.CharField(max_length=254, blank=True, db_index=True)
    total_deud = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    deuda_mese = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    medidor = models.CharField(max_length=100, blank=True)
    atributos_originales = models.JSONField(default=dict)
    geom = models.MultiPolygonField(srid=32717, spatial_index=True)
    geometria_valida = models.BooleanField(default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['version', 'source_fid'], name='predio_version_fid')]
        indexes = [models.Index(fields=['version', 'parroquia', 'zona', 'sector'])]
