from rest_framework import serializers
from .models import Herramienta, Contratista, Prestamo, Mantenimiento

class HerramientaSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    alerta_mantenimiento = serializers.SerializerMethodField()

    class Meta:
        model = Herramienta
        fields = '__all__'

    def get_alerta_mantenimiento(self, obj):
        return obj.requiere_mantenimiento()


class ContratistaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contratista
        fields = '__all__'


class PrestamoSerializer(serializers.ModelSerializer):
    herramienta_nombre = serializers.CharField(source='herramienta.nombre', read_only=True)
    herramienta_codigo = serializers.CharField(source='herramienta.codigo_interno', read_only=True)
    contratista_nombre = serializers.CharField(source='contratista.nombre_empresa', read_only=True)
    responsable_obra = serializers.CharField(source='contratista.responsable_obra', read_only=True)
    esta_atrasado = serializers.BooleanField(read_only=True)

    class Meta:
        model = Prestamo
        fields = '__all__'

    def validate(self, data):
        # Validaciones al crear un nuevo préstamo (Entrega de herramienta)
        if self.instance is None:
            herramienta = data.get('herramienta')
            contratista = data.get('contratista')

            # Verificar y actualizar morosidad en tiempo real
            if contratista.verificar_morosidad():
                raise serializers.ValidationError(
                    f"ALERTA DE MOROSIDAD: El contratista '{contratista.nombre_empresa}' está BLOQUEADO por tener préstamos vencidos o estado moroso."
                )

            if herramienta.estado != 'DISPONIBLE':
                raise serializers.ValidationError(
                    f"La herramienta '{herramienta.nombre}' no se puede entregar porque su estado actual es: {herramienta.get_estado_display()}."
                )
        return data


class MantenimientoSerializer(serializers.ModelSerializer):
    herramienta_nombre = serializers.CharField(source='herramienta.nombre', read_only=True)
    herramienta_codigo = serializers.CharField(source='herramienta.codigo_interno', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Mantenimiento
        fields = '__all__'