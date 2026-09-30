from django.db import models
from django.contrib.auth.models import User

# ==========================================
# 1. MODELO DE MAQUINARIA (CATÁLOGO)
# ==========================================
class Maquinaria(models.Model):
    nombre = models.CharField(max_length=150)
    categoria = models.CharField(max_length=100)
    tarifa_diaria = models.DecimalField(max_digits=10, decimal_places=0) # Usamos 0 decimales para pesos chilenos
    garantia_fija = models.DecimalField(max_digits=10, decimal_places=0)
    stock_disponible = models.PositiveIntegerField(default=0)
    imagen_url = models.URLField(max_length=800, blank=True, null=True, default="https://via.placeholder.com/400x300?text=Sin+Imagen")
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - Stock: {self.stock_disponible}"

# ==========================================
# 2. MODELO DE CARRO PERSISTENTE
# ==========================================
class CarroArriendo(models.Model):
    # Cumple el requisito: Relación 1 a 1 entre Usuario y su Carro activo
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carro')
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carro de {self.usuario.username}"

class ItemCarro(models.Model):
    carro = models.ForeignKey(CarroArriendo, on_delete=models.CASCADE, related_name='items')
    maquinaria = models.ForeignKey(Maquinaria, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    cantidad = models.PositiveIntegerField(default=1)

    # Este es el cálculo matemático que pide la pauta para el costo del ítem
    @property
    def dias_arriendo(self):
        dias = (self.fecha_fin - self.fecha_inicio).days
        return dias if dias > 0 else 1

    @property
    def subtotal(self):
        return (self.maquinaria.tarifa_diaria * self.dias_arriendo) + self.maquinaria.garantia_fija

# ==========================================
# 3. MODELO DE CONTRATOS (TRANSACCIÓN FINAL)
# ==========================================
class Contrato(models.Model):
    # Cumple el requisito OBLIGATORIO: Implementación explícita de propiedad CHOICES
    ESTADOS_CONTRATO = [
        ('PENDIENTE', 'Pendiente de Pago'),
        ('PAGADO', 'Pagado (Stock Descontado)'),
        ('ENTREGADO', 'Equipo Entregado al Cliente'),
        ('COMPLETADO', 'Devuelto (Stock Reincorporado)'),
        ('CANCELADO', 'Cancelado (Stock Liberado)'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS_CONTRATO, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    total_pagar = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    def __str__(self):
        return f"Contrato #{self.id} - {self.usuario.username} - {self.estado}"

class DetalleContrato(models.Model):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='detalles')
    maquinaria = models.ForeignKey(Maquinaria, on_delete=models.PROTECT)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    cantidad = models.PositiveIntegerField(default=1)
    precio_congelado = models.DecimalField(max_digits=12, decimal_places=0) # Guarda el costo exacto al momento de pagar


