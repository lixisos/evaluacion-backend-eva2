# Registro de Consultas y Apoyo de Inteligencia Artificial (EVA 3)

**Estudiante:** Bastian Andres Fernandez Neira  
**Sección:** AP-N4-C2  
**Proyecto Asignado:** Proyecto 4 - Sistema de Alquiler y Control de Herramientas (BuildCorp)  

---

## 1. Diseño de Modelos Relacionales y Reglas de Negocio
* **Prompt utilizado:** *"Necesito estructurar los modelos en Django para el caso BuildCorp (Proyecto 4) con PostgreSQL. Debe incluir catálogo de herramientas con estados (Disponible, En Uso, Mantenimiento, Dado de Baja), subcontratistas con bloqueo automático por morosidad, préstamos con firma digital en Base64 y programación de mantenimientos preventivos por horas de uso o fecha."*
* **Resultado / Apoyo obtenido:** Generación de las clases `Herramienta`, `Contratista`, `Prestamo` y `Mantenimiento` en `app/models.py`, incorporando métodos de validación como `requiere_mantenimiento()` y `verificar_morosidad()`.

## 2. Personalización de Django Admin
* **Prompt utilizado:** *"Cómo personalizar el panel de Django Admin para los 4 modelos de BuildCorp agregando filtros laterales (list_filter), barras de búsqueda (search_fields), insignias de colores por estado y previsualización de la firma digital en Base64."*
* **Resultado / Apoyo obtenido:** Implementación en `app/admin.py` utilizando `format_html` para renderizar etiquetas de estado de trazabilidad, alertas visuales de morosidad y miniaturas de la firma digital del responsable de obra.

## 3. Endpoints DRF y Lógica Transaccional
* **Prompt utilizado:** *"Crear los serializadores y ViewSets en Django REST Framework para gestionar el préstamo y devolución de herramientas con transaction.atomic(), cambiando automáticamente el activo a MANTENIMIENTO si supera el límite de horas de uso al devolverse."*
* **Resultado / Apoyo obtenido:** Codificación de `app/serializers.py` y `app/views.py` con las acciones personalizadas `@action` para `registrar_devolucion`, `verificar_alertas_morosidad`, `alternar_bloqueo` y `completar` mantenimiento.

## 4. Interfaz Frontend y Captura de Firma Digital en HTML5 Canvas
* **Prompt utilizado:** *"Generar una interfaz web responsiva con Bootstrap 5 en un template de Django que consuma la API mediante fetch(), incluyendo un elemento HTML5 Canvas interactivo para dibujar la firma digital en la entrega y devolución de herramientas."*
* **Resultado / Apoyo obtenido:** Construcción de `templates/catalogo.html` con pestañas dinámicas y script de captura de trazos en `<canvas>` exportados mediante `toDataURL('image/png')`.

## 5. Script de Despliegue en AWS EC2 con PostgreSQL
* **Prompt utilizado:** *"Proporcionar la secuencia de comandos Bash para configurar Ubuntu Server en una instancia AWS EC2 única, instalando PostgreSQL local, entorno virtual Python, migraciones de Django y ejecución del servidor expuesto en el puerto 8000/80."*
* **Resultado / Apoyo obtenido:** Comandos de aprovisionamiento para PostgreSQL (`sudo -u postgres psql`), instalación de dependencias y ejecución del proyecto en producción dentro de AWS Academy.