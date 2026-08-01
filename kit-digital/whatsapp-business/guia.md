# WhatsApp Business — guía de alta

**Objetivo:** un solo número comercial argentino que centralice leads, presupuestos y posventa. Es el canal de cierre nº 1 del negocio (ver GTM del PDF).

## 1. Línea
1. Comprar un chip nuevo a nombre de la empresa o de Ignacio (Movistar/Personal/Claro, plan con datos). **No usar el número personal de Ignacio**: el número comercial debe poder transferirse/atenderse por un empleado en el futuro.
2. Formato final: `+54 9 11 XXXX-XXXX`.

## 2. Alta de la app
1. Instalar **WhatsApp Business** (app gratuita, no la normal) en el teléfono de trabajo.
2. Registrar el número nuevo → nombre de empresa: **Clima Baires** (no se puede cambiar fácil: revisar tildes).
3. Categoría: *Servicio de aire acondicionado y calefacción*.

## 3. Perfil (copiar y pegar)
- **Foto:** `../assets/avatar-1080.png` (WhatsApp la recorta en círculo; el isotipo queda centrado).
- **Descripción:** `Venta, instalación certificada y posventa de aire acondicionado en el corredor norte: Núñez, Vicente López, San Isidro, Tigre, Nordelta y Pilar. Presupuesto en el día. Tu confort, nuestra prioridad.`
- **Dirección:** dejar VACÍA (trabajamos a domicilio, sin local).
- **Horario:** Lun a Sáb 08:00–19:00.
- **Email:** info@climabaires.com · **Web:** https://climabaires.com

## 4. Mensajes automáticos
**Bienvenida** (Configuración → Herramientas de empresa → Mensaje de bienvenida):
> ¡Hola! Somos Clima Baires ❄️ Gracias por escribirnos. Contanos: 1️⃣ ¿Instalación nueva, recambio o service? 2️⃣ ¿En qué zona estás? 3️⃣ Si podés, mandanos una foto del ambiente y otra del exterior (donde iría la condensadora). Con eso te pasamos presupuesto hoy mismo.

**Ausencia** (fuera de horario):
> Gracias por tu mensaje 🙌 Nuestro horario es de lunes a sábado de 8 a 19 h. Te respondemos a primera hora. Si es una urgencia de un equipo instalado por nosotros, escribí URGENTE y lo vemos antes.

## 5. Respuestas rápidas (atajos con «/»)
| Atajo | Texto |
|---|---|
| /presupuesto | Para pasarte un presupuesto cerrado necesitamos: m² del ambiente, piso, orientación y 2 fotos (interior + exterior). Si preferís, calculá tus frigorías acá: https://climabaires.com/calculadora-frigorias.html |
| /zonas | Trabajamos en Núñez, Vicente López, San Isidro, Tigre (incluida Nordelta) y Pilar. Visita técnica sin cargo en toda la zona. |
| /pago | Aceptamos transferencia (con descuento), tarjetas de débito/crédito y cuotas. Con el presupuesto te detallamos cada opción con su precio final. |
| /country | Ingresamos a countries y barrios cerrados con seguros al día (AP + RC con cláusula de no repetición). Pasanos el barrio y coordinamos el alta de proveedor si hace falta. |
| /service | Hacemos mantenimiento y reparación multimarca: limpieza profunda, control de gas y repuestos originales. ¿Qué equipo tenés y qué le pasa? |
| /gracias | ¡Gracias por elegirnos! 🙌 Si quedaste conforme, nos ayuda muchísimo una reseña en Google: [PEGAR LINK CORTO DE RESEÑA — ver guía google-business] |

## 6. Etiquetas (embudo)
`🆕 Lead` → `📋 Presupuesto enviado` → `📅 Agendado` → `✅ Instalado` → `🔧 Posventa` + etiqueta transversal `🏘️ Country`.
Regla operativa: **ningún chat sin etiqueta**; revisar cada mañana los `📋` de más de 48 h y hacer seguimiento.

## 7. Catálogo (5 ítems iniciales — precio «desde», actualizar mensualmente)
1. Instalación split hasta 3.000 frigorías — instalación estándar hasta 3 m de cañería, vacío y prueba incluidos.
2. Instalación split 4.500–6.500 frigorías.
3. Equipo + instalación llave en mano — split inverter gama media/alta, precio cerrado.
4. Mantenimiento preventivo anual — limpieza profunda + control de gas.
5. Visita técnica y diagnóstico — sin cargo en el corredor norte (se descuenta del trabajo).

## 8. Después del alta
1. Generar el **link corto** (Configuración → Herramientas → Enlace corto) y el **QR**.
2. **Actualizar `web/assets/js/main.js`** con el número real (2 campos: `whatsapp` y `whatsappVisible`).
3. Imprimir el QR en tarjetas/remitos (pedir reseña + recontacto).
4. Cuando haya >30-50 conversaciones/día, evaluar WhatsApp Business API con un proveedor (360dialog €49/mes o Wasapi ~US$30/mes) para plantillas y multiagente — no antes.
