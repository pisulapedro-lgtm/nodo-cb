# Clima Baires — ecommerce

Tienda online de **venta e instalación** de equipos de climatización en la
Costa del Sol (Málaga).

**Modelo:** empresa instaladora en activo, con instaladores propios habilitados,
abriendo canal de venta online. El producto es el equipo **instalado y
funcionando**, con precio cerrado — no la caja.

## Estado

Sprint de lanzamiento: semana del 3 al 9 de agosto de 2026.
Objetivo: tienda completa en modo privado, lista para revisar el viernes 7.

## Documentación

- **[Plan de ejecución — semana 1](docs/PLAN-SEMANA-1.md)** — el plan día a día
  que se está siguiendo. Empezar por acá.
- [Plan técnico](docs/PLAN-TECNICO.md) — arquitectura, elección de plataforma,
  sincronizador multi-proveedor y cumplimiento normativo UE/España.
  Escrito antes de confirmar el contexto de negocio: algunos supuestos quedaron
  superados por el plan de semana 1.

## Decisiones tomadas

| | |
|---|---|
| Plataforma | Shopify (plan Basic), tema Dawn |
| Zona | Costa del Sol, validación por código postal |
| Catálogo inicial | 30-40 SKUs: split 1x1, multisplit, conductos y cassette |
| Idiomas | Español + inglés (mercado residente extranjero) |
| Instalación | Propia, incluida en el precio mostrado |
| Conductos y cassette | Solicitud de presupuesto, no compra directa |

## Puntos de atención

1. **EPREL** — el ID de la base de datos energética de la UE es obligatorio para
   venta online. Ningún producto se publica sin él.
2. **RAEE** — retirada gratuita del equipo antiguo (recogida uno por uno).
3. **Legales** — los borradores requieren revisión del gestor antes de publicar.
4. **Cobertura** — nunca prometer instalación fuera de la zona cubierta.
