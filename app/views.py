from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from .models import Maquinaria, CarroArriendo, ItemCarro, Contrato, DetalleContrato
from .serializers import (MaquinariaSerializer, CarroArriendoSerializer, ItemCarroSerializer, ContratoSerializer, CustomTokenObtainPairSerializer)
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action

# AUTENTICACIÓN (INYECCIÓN DE ROLES)
class CustomTokenObtainPairView(TokenObtainPairView):
    # Usa nuestro serializador personalizado para incluir "Empresa Constructora" o "Ejecutivo" en el Token
    serializer_class = CustomTokenObtainPairSerializer

# CATALOGO DE MAQUINARIA (CON FILTROS)
class MaquinariaViewSet(viewsets.ModelViewSet):
    queryset = Maquinaria.objects.all()
    serializer_class = MaquinariaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['categoria'] # Filtro exigido por la pauta
    
    def get_permissions(self):
        # Cualquiera puede leer el catálogo, pero solo los administradores (Ejecutivos) pueden modificarlo
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
    
# GESTIÓN DEL CARRO PERSISTENTE
class MiCarroView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Busca el carro del usuario, si no existe, lo crea. (Cumple relación 1 a 1 y persistencia)
        carro, _ = CarroArriendo.objects.get_or_create(usuario=request.user)
        serializer = CarroArriendoSerializer(carro)
        return Response(serializer.data)

class ItemCarroViewSet(viewsets.ModelViewSet):
    serializer_class = ItemCarroSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Un usuario solo puede ver los ítems de SU propio carro
        return ItemCarro.objects.filter(carro__usuario=self.request.user)

    def perform_create(self, serializer):
        carro, _ = CarroArriendo.objects.get_or_create(usuario=self.request.user)
        serializer.save(carro=carro)
        
# CHECKOUT (GENERACION DE LA ORDEN)
class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        carro = getattr(request.user, 'carro', None)
        if not carro or not carro.items.exists():
            return Response({"error": "El carro está vacío"}, status=status.HTTP_400_BAD_REQUEST)

        # transaction.atomic() bloquea la base de datos para que no haya errores si dos personas compran a la vez
        with transaction.atomic():
            total = sum(item.subtotal for item in carro.items.all())
            contrato = Contrato.objects.create(usuario=request.user, total_pagar=total)
            
            for item in carro.items.all():
                if item.maquinaria.stock_disponible < item.cantidad:
                     return Response({"error": f"No hay suficiente stock para la máquina {item.maquinaria.nombre}. Stock actual: {item.maquinaria.stock_disponible}"}, status=status.HTTP_400_BAD_REQUEST)

                DetalleContrato.objects.create(
                    contrato=contrato,
                    maquinaria=item.maquinaria,
                    fecha_inicio=item.fecha_inicio,
                    fecha_fin=item.fecha_fin,
                    cantidad=item.cantidad, # Guardamos la cantidad en el contrato
                    precio_congelado=item.subtotal
                )
            # Limpiamos el carro tras generar el contrato exitosamente
            carro.items.all().delete()

        serializer = ContratoSerializer(contrato)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


#  CONTRATOS Y LÓGICA TRANSACCIONAL DE STOCK
class ContratoViewSet(viewsets.ModelViewSet):
    serializer_class = ContratoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff: 
            return Contrato.objects.all()
        return Contrato.objects.filter(usuario=self.request.user)

    # NUEVO: Ruta personalizada para procesar el pago directamente aquí
    @action(detail=False, methods=['post'], url_path='checkout')
    def procesar_checkout(self, request):
        carro = getattr(request.user, 'carro', None)
        if not carro or not carro.items.exists():
            return Response({"error": "El carro está vacío"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Sumar el subtotal de cada ítem (que ya viene multiplicado por la cantidad en el serializer)
            total = sum(item.subtotal for item in carro.items.all())
            contrato = Contrato.objects.create(usuario=request.user, total_pagar=total)

            for item in carro.items.all():
                if item.maquinaria.stock_disponible < item.cantidad:
                     return Response({"error": f"No hay stock suficiente para {item.maquinaria.nombre}."}, status=status.HTTP_400_BAD_REQUEST)

                DetalleContrato.objects.create(
                    contrato=contrato,
                    maquinaria=item.maquinaria,
                    fecha_inicio=item.fecha_inicio,
                    fecha_fin=item.fecha_fin,
                    cantidad=item.cantidad,
                    precio_congelado=item.subtotal
                )
            # Vaciar el carro
            carro.items.all().delete()

        return Response({"mensaje": "Contrato creado con éxito"}, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        contrato = self.get_object()
        nuevo_estado = request.data.get('estado')

        if not request.user.is_staff:
            return Response({"error": "Solo un Ejecutivo puede actualizar el estado"}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            if nuevo_estado == 'PAGADO' and contrato.estado == 'PENDIENTE':
                for detalle in contrato.detalles.all():
                    maquina = detalle.maquinaria
                    if maquina.stock_disponible < detalle.cantidad:
                        return Response({"error": f"Stock insuficiente para {maquina.nombre}"}, status=status.HTTP_400_BAD_REQUEST)
                    maquina.stock_disponible -= detalle.cantidad
                    maquina.save()
            
            elif nuevo_estado in ['COMPLETADO', 'CANCELADO'] and contrato.estado == 'PAGADO':
                for detalle in contrato.detalles.all():
                    maquina = detalle.maquinaria
                    maquina.stock_disponible += detalle.cantidad
                    maquina.save()
            
            return super().partial_update(request, *args, **kwargs)

# VISTAS FRONTEND (ENMASCARAMIENTO)
def login_view(request):
    return render(request, 'login.html')

def catalogo_view(request):
    return render(request, 'catalogo.html')

def carro_view(request):
    return render(request, 'carro.html')

def dashboard_view(request):
    return render(request, 'dashboard.html')


@api_view(['POST'])
@permission_classes([AllowAny])
def registro_cliente(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({"error": "Faltan datos"}, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(username=username).exists():
        return Response({"error": "El usuario ya existe"}, status=status.HTTP_400_BAD_REQUEST)
        
    # Crear usuario normal (is_staff=False, por lo tanto es Cliente)
    user = User.objects.create_user(username=username, password=password)
    return Response({"mensaje": "Usuario creado"}, status=status.HTTP_201_CREATED)

# Vista para renderizar el HTML del registro
def registro_view(request):
    return render(request, 'registro.html')