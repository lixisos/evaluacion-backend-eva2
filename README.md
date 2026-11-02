# 🏗️ BuildCorp - Sistema de Alquiler y Control de Herramientas (EVA 3 Backend)

* **Estudiante:** Bastian Andres Fernandez Neira
* **Sección:** AP-N4-C2
* **Asignatura:** Desarrollo Backend - INACAP (2026)
* **Proyecto Asignado:** Proyecto 4 (BuildCorp)

## 🌐 Acceso Despliegue en AWS EC2
* **Aplicación Web Pública:** http://34.229.173.105:8000/
* **Panel Administrativo (Django Admin):** http://34.229.173.105:8000/admin/
* **Documentación OpenAPI (Swagger):** http://34.229.173.105:8000/api/docs/

## 🚀 Funcionalidades Implementadas
1. **Catálogo y Trazabilidad de Activos:** Control de herramientas por código, categoría, ubicación en bodega/obra y estados (`DISPONIBLE`, `EN_USO`, `MANTENIMIENTO`, `DADO_DE_BAJA`).
2. **Entrega y Devolución con Firma Digital:** Registro de préstamos con captura de firma digital en HTML5 Canvas (`Base64`) tanto al retirar como al devolver el equipo.
3. **Mantenimiento Preventivo Automatizado:** Control de horas de uso acumuladas y fechas límite; envío automático a taller cuando un activo alcanza su umbral de horas tras una devolución.
4. **Alertas de Morosidad y Bloqueo Automático:** Detección de préstamos vencidos y bloqueo inmediato de subcontratistas morosos impidiendo nuevos retiros.

## 🛠️ Instrucciones de Ejecución Local / EC2
```bash
python -m venv venv
source venv/bin/activate  # En Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000