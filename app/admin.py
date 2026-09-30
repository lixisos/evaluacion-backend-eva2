from django.contrib import admin
from .models import Maquinaria, CarroArriendo, ItemCarro, Contrato, DetalleContrato

admin.site.register(Maquinaria)
admin.site.register(CarroArriendo)
admin.site.register(ItemCarro)
admin.site.register(Contrato)
admin.site.register(DetalleContrato)