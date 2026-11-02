from django.contrib import admin
from django.utils.html import format_html
from .models import Herramienta, Contratista, Prestamo, Mantenimiento

@admin.register(Herramienta)
class HerramientaAdmin(admin.ModelAdmin):
    list_display = ('codigo_interno', 'nombre', 'categoria', 'bodega_obra', 'estado_badge', 'horas_uso_acumuladas', 'fecha_proximo_mantenimiento')
    list_filter = ('estado', 'categoria', 'bodega_obra')
    search_fields = ('codigo_interno', 'nombre', 'categoria', 'bodega_obra')
    ordering = ('codigo_interno',)

    def estado_badge(self, obj):
        colores = {
            'DISPONIBLE': 'green',
            'EN_USO': 'blue',
            'MANTENIMIENTO': 'orange',
            'DADO_DE_BAJA': 'red',
        }
        color = colores.get(obj.estado, 'black')
        return format_html('<b style="color: {};">{}</b>', color, obj.get_estado_display())
    estado_badge.short_description = 'Estado Trazabilidad'


@admin.register(Contratista)
class ContratistaAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre_empresa', 'responsable_obra', 'telefono', 'email', 'estado_morosidad')
    list_filter = ('bloqueado_por_morosidad',)
    search_fields = ('rut', 'nombre_empresa', 'responsable_obra')

    def estado_morosidad(self, obj):
        if obj.bloqueado_por_morosidad:
            return format_html('<span style="color: white; background-color: red; padding: 3px 8px; border-radius: 4px; font-weight: bold;">BLOQUEADO (MOROSO)</span>')
        return format_html('<span style="color: green; font-weight: bold;">Al Día / Habilitado</span>')
    estado_morosidad.short_description = 'Estado Morosidad'


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('id', 'herramienta', 'contratista', 'obra_destino', 'fecha_entrega', 'fecha_devolucion_esperada', 'estado', 'preview_firma')
    list_filter = ('estado', 'fecha_entrega', 'obra_destino')
    search_fields = ('herramienta__nombre', 'herramienta__codigo_interno', 'contratista__nombre_empresa', 'obra_destino')

    def preview_firma(self, obj):
        if obj.firma_digital_entrega:
            return format_html('<img src="{}" style="height: 35px; border: 1px solid #ccc; background: #fff;" />', obj.firma_digital_entrega)
        return "Sin firma"
    preview_firma.short_description = 'Firma Responsable'


@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'herramienta', 'tipo', 'fecha_programada', 'tecnico_responsable', 'costo', 'estado')
    list_filter = ('tipo', 'estado', 'fecha_programada')
    search_fields = ('herramienta__nombre', 'herramienta__codigo_interno', 'tecnico_responsable')