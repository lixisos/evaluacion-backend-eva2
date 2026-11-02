from django.db import models
from django.utils import timezone

# 1. MODELO DE HERRAMIENTAS / ACTIVOS
class Herramienta(models.Model):
    ESTADOS_ACTIVO = (
        ('DISPONIBLE', 'Disponible'),
        ('EN_USO', 'En Uso'),
        ('MANTENIMIENTO', 'Mantenimiento'),
        ('DADO_DE_BAJA', 'Dado de Baja'),
    )

    codigo_interno = models.CharField(max_length=50, unique=True, verbose_name="Código de Activo")
    nombre = models.CharField(max_length=150, verbose_name="Nombre de Herramienta")
    categoria = models.CharField(max_length=100, verbose_name="Categoría (Ej. Eléctrica, Pesada)")
    bodega_obra = models.CharField(max_length=120, default="Bodega Central", verbose_name="Bodega / Obra Actual")
    estado = models.CharField(max_length=20, choices=ESTADOS_ACTIVO, default='DISPONIBLE')
    tarifa_diaria = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    horas_uso_acumuladas = models.PositiveIntegerField(default=0, verbose_name="Horas de Uso")
    limite_horas_mantenimiento = models.PositiveIntegerField(default=100, verbose_name="Límite Hrs para Mantenimiento")
    fecha_proximo_mantenimiento = models.DateField(null=True, blank=True, verbose_name="Próximo Mantenimiento")

    def requiere_mantenimiento(self):
        por_horas = self.horas_uso_acumuladas >= self.limite_horas_mantenimiento
        por_fecha = self.fecha_proximo_mantenimiento is not None and self.fecha_proximo_mantenimiento <= timezone.now().date()
        return por_horas or por_fecha

    def __str__(self):
        return f"[{self.codigo_interno}] {self.nombre} - {self.get_estado_display()}"


# 2. MODELO DE SUBCONTRATISTAS / RESPONSABLES DE OBRA
class Contratista(models.Model):
    rut = models.CharField(max_length=20, unique=True, verbose_name="RUT Empresa/Contratista")
    nombre_empresa = models.CharField(max_length=150, verbose_name="Empresa Subcontratista")
    responsable_obra = models.CharField(max_length=150, verbose_name="Responsable de Obra")
    telefono = models.CharField(max_length=30)
    email = models.EmailField()
    bloqueado_por_morosidad = models.BooleanField(default=False, verbose_name="Bloqueado por Morosidad")

    def verificar_morosidad(self):
        """Revisa si tiene préstamos activos vencidos y bloquea automáticamente."""
        hoy = timezone.now().date()
        prestamos_vencidos = self.prestamos.filter(estado='ACTIVO', fecha_devolucion_esperada__lt=hoy).exists()
        if prestamos_vencidos and not self.bloqueado_por_morosidad:
            self.bloqueado_por_morosidad = True
            self.save(update_fields=['bloqueado_por_morosidad'])
        return self.bloqueado_por_morosidad

    def __str__(self):
        estado = "BLOQUEADO (MOROSO)" if self.bloqueado_por_morosidad else "HABILITADO"
        return f"{self.nombre_empresa} ({self.responsable_obra}) - {estado}"


# 3. MODELO DE PRÉSTAMOS (ENTREGA Y DEVOLUCIÓN CON FIRMA DIGITAL)
class Prestamo(models.Model):
    ESTADOS_PRESTAMO = (
        ('ACTIVO', 'Activo (En Obra)'),
        ('DEVUELTO', 'Devuelto a Bodega'),
        ('ATRASADO', 'En Morosidad / Atrasado'),
    )

    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE, related_name='prestamos')
    contratista = models.ForeignKey(Contratista, on_delete=models.CASCADE, related_name='prestamos')
    obra_destino = models.CharField(max_length=150, verbose_name="Obra de Destino")
    fecha_entrega = models.DateField(default=timezone.now)
    fecha_devolucion_esperada = models.DateField(verbose_name="Fecha Límite Devolución")
    fecha_devolucion_real = models.DateField(null=True, blank=True, verbose_name="Fecha Devolución Real")
    horas_usadas_en_prestamo = models.PositiveIntegerField(default=0, verbose_name="Horas de Uso en Obra")
    estado = models.CharField(max_length=20, choices=ESTADOS_PRESTAMO, default='ACTIVO')
    firma_digital_entrega = models.TextField(verbose_name="Firma Digital Entrega (Base64)")
    firma_digital_devolucion = models.TextField(null=True, blank=True, verbose_name="Firma Digital Devolución (Base64)")
    observaciones = models.TextField(blank=True, null=True)

    @property
    def esta_atrasado(self):
        if self.estado == 'ACTIVO' and self.fecha_devolucion_esperada < timezone.now().date():
            return True
        return self.estado == 'ATRASADO'

    def __str__(self):
        return f"Préstamo #{self.id} - {self.herramienta.nombre} a {self.contratista.nombre_empresa}"


# 4. MODELO DE MANTENIMIENTOS PREVENTIVOS Y HOJA DE VIDA
class Mantenimiento(models.Model):
    TIPOS_MANTENIMIENTO = (
        ('PREVENTIVO', 'Preventivo (Por Horas/Fecha)'),
        ('CORRECTIVO', 'Correctivo (Falla en Obra)'),
    )
    ESTADOS_MANTENIMIENTO = (
        ('PROGRAMADO', 'Programado'),
        ('EN_PROCESO', 'En Taller / En Proceso'),
        ('COMPLETADO', 'Completado (Equipo Liberado)'),
    )

    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE, related_name='mantenimientos')
    tipo = models.CharField(max_length=20, choices=TIPOS_MANTENIMIENTO, default='PREVENTIVO')
    fecha_programada = models.DateField(default=timezone.now)
    tecnico_responsable = models.CharField(max_length=120, verbose_name="Técnico / Taller")
    descripcion_trabajo = models.TextField(verbose_name="Detalle técnico / Hoja de Vida")
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS_MANTENIMIENTO, default='PROGRAMADO')

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.herramienta.nombre} ({self.get_estado_display()})"