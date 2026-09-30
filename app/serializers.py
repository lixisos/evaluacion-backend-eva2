from rest_framework import serializers
from .models import Maquinaria, CarroArriendo, ItemCarro, Contrato, DetalleContrato
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# 1. SERIALIZADOR DEL CATÁLOGO
class MaquinariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maquinaria
        fields = '__all__'

# 2. SERIALIZADORES DEL CARRO Y SUS ÍTEMS
class ItemCarroSerializer(serializers.ModelSerializer):
    # Traemos las propiedades matemáticas que calculan los días y el subtotal desde el modelo
    dias_arriendo = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()
    # Anidamos los detalles de la máquina para que el frontend vea el nombre y no solo el ID
    maquinaria_detalle = MaquinariaSerializer(source='maquinaria', read_only=True)

    class Meta:
        model = ItemCarro
        fields = ['id', 'maquinaria', 'maquinaria_detalle', 'fecha_inicio', 'fecha_fin', 'cantidad', 'dias_arriendo', 'subtotal']

class CarroArriendoSerializer(serializers.ModelSerializer):
    items = ItemCarroSerializer(many=True, read_only=True)

    class Meta:
        model = CarroArriendo
        fields = ['id', 'usuario', 'creado_en', 'items']

# 3. SERIALIZADORES DEL CONTRATO (CHECKOUT)
class DetalleContratoSerializer(serializers.ModelSerializer):
    maquinaria_detalle = MaquinariaSerializer(source='maquinaria', read_only=True)

    class Meta:
        model = DetalleContrato
        fields = ['id', 'maquinaria', 'maquinaria_detalle', 'fecha_inicio', 'fecha_fin', 'precio_congelado']

class ContratoSerializer(serializers.ModelSerializer):
    detalles = DetalleContratoSerializer(many=True, read_only=True)

    class Meta:
        model = Contrato
        fields = ['id', 'usuario', 'estado', 'fecha_creacion', 'total_pagar', 'detalles']

# 4. SERIALIZADOR CUSTOM PARA EL TOKEN JWT (Inyectar Roles)
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Inyectamos los claims personalizados exigidos por la pauta
        token['username'] = user.username
        token['email'] = user.email
        
        # Validamos el rol basándonos en si el usuario es parte del Staff (Ejecutivo) o no (Empresa Constructora)
        if user.is_staff:
            token['rol'] = 'Ejecutivo de Arriendos'
        else:
            token['rol'] = 'Empresa Constructora'

        return token

