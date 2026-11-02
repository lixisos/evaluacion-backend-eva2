from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Herramienta, Contratista, Prestamo, Mantenimiento
from .serializers import (
    HerramientaSerializer, ContratistaSerializer,
    PrestamoSerializer, MantenimientoSerializer
)

# === VISTAS HTML Y SESIONES DE USUARIO ===

def index_view(request):
    """Renderiza el panel principal de BuildCorp."""
    return render(request, 'catalogo.html')

def login_view(request):
    """Manejo de sesión para operadores y administradores."""
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('home')
        return render(request, 'login.html', {'error': 'Credenciales inválidas'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')


# === ENDPOINTS API REST (DRF) & REGLAS DE NEGOCIO ===

class HerramientaViewSet(viewsets.ModelViewSet):
    queryset = Herramienta.objects.all().order_by('codigo_interno')
    serializer_class = HerramientaSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['estado', 'categoria', 'bodega_obra']


class ContratistaViewSet(viewsets.ModelViewSet):
    queryset = Contratista.objects.all().order_by('nombre_empresa')
    serializer_class = ContratistaSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'])
    def alternar_bloqueo(self, request, pk=None):
        """Permite bloquear o desbloquear manualmente a un contratista."""
        contratista = self.get_object()
        contratista.bloqueado_por_morosidad = not contratista.bloqueado_por_morosidad
        contratista.save()
        return Response({
            'id': contratista.id,
            'bloqueado_por_morosidad': contratista.bloqueado_por_morosidad
        })


class PrestamoViewSet(viewsets.ModelViewSet):
    queryset = Prestamo.objects.all().order_by('-id')
    serializer_class = PrestamoSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def perform_create(self, serializer):
        """Al entregar una herramienta, cambia su estado a EN_USO y actualiza su ubicación."""
        prestamo = serializer.save()
        herramienta = prestamo.herramienta
        herramienta.estado = 'EN_USO'
        herramienta.bodega_obra = prestamo.obra_destino
        herramienta.save()

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def registrar_devolucion(self, request, pk=None):
        """Registra la devolución con firma digital, suma horas de uso y evalúa mantenimiento."""
        prestamo = self.get_object()
        if prestamo.estado == 'DEVUELTO':
            return Response({'error': 'Este préstamo ya fue devuelto anteriormente.'}, status=status.HTTP_400_BAD_REQUEST)

        firma_devolucion = request.data.get('firma_digital_devolucion')
        horas_usadas = int(request.data.get('horas_usadas_en_prestamo', 0))
        bodega_retorno = request.data.get('bodega_retorno', 'Bodega Central')

        if not firma_devolucion:
            return Response({'error': 'La firma digital del responsable es obligatoria para devolver.'}, status=status.HTTP_400_BAD_REQUEST)

        prestamo.firma_digital_devolucion = firma_devolucion
        prestamo.horas_usadas_en_prestamo = horas_usadas
        prestamo.fecha_devolucion_real = timezone.now().date()
        prestamo.estado = 'DEVUELTO'
        prestamo.save()

        # Actualizar trazabilidad y horas de uso de la herramienta
        herramienta = prestamo.herramienta
        herramienta.horas_uso_acumuladas += horas_usadas
        herramienta.bodega_obra = bodega_retorno

        # Regla 3: Si superó las horas límite o fecha, pasa automáticamente a MANTENIMIENTO
        if herramienta.requiere_mantenimiento():
            herramienta.estado = 'MANTENIMIENTO'
            Mantenimiento.objects.create(
                herramienta=herramienta,
                tipo='PREVENTIVO',
                tecnico_responsable='Taller Central BuildCorp',
                descripcion_trabajo=f'Mantenimiento preventivo automático por alcanzar {herramienta.horas_uso_acumuladas} hrs de uso.',
                estado='PROGRAMADO'
            )
        else:
            herramienta.estado = 'DISPONIBLE'
        herramienta.save()

        return Response({'mensaje': 'Devolución registrada con éxito.', 'nuevo_estado_herramienta': herramienta.estado})

    @action(detail=False, methods=['post'])
    def verificar_alertas_morosidad(self, request):
        """Revisa todos los préstamos vencidos, los marca como ATRASADO y bloquea al contratista."""
        hoy = timezone.now().date()
        vencidos = Prestamo.objects.filter(estado='ACTIVO', fecha_devolucion_esperada__lt=hoy)
        bloqueados = 0
        for p in vencidos:
            p.estado = 'ATRASADO'
            p.save()
            if not p.contratista.bloqueado_por_morosidad:
                p.contratista.bloqueado_por_morosidad = True
                p.contratista.save()
                bloqueados += 1
        return Response({
            'prestamos_en_mora': Prestamo.objects.filter(estado='ATRASADO').count(),
            'nuevos_contratistas_bloqueados': bloqueados
        })


class MantenimientoViewSet(viewsets.ModelViewSet):
    queryset = Mantenimiento.objects.all().order_by('-id')
    serializer_class = MantenimientoSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def perform_create(self, serializer):
        """Al registrar un mantenimiento, la herramienta pasa a estado MANTENIMIENTO."""
        mant = serializer.save()
        if mant.estado != 'COMPLETADO':
            h = mant.herramienta
            h.estado = 'MANTENIMIENTO'
            h.save()

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def completar(self, request, pk=None):
        """Finaliza el mantenimiento, reinicia contador o libera la herramienta a DISPONIBLE."""
        mant = self.get_object()
        mant.estado = 'COMPLETADO'
        mant.save()

        h = mant.herramienta
        h.estado = 'DISPONIBLE'
        h.limite_horas_mantenimiento = h.horas_uso_acumuladas + 100
        h.save()
        return Response({'mensaje': 'Mantenimiento completado. Herramienta nuevamente DISPONIBLE.'})