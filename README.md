# nodo-cb

Ecommerce de equipos de climatización (aire acondicionado) para el mercado español.

**Modelo:** venta sin stock propio — la compra al proveedor se genera a partir de la venta.
Catálogo alimentado por varios proveedores mayoristas.

## Estado

Fase de definición técnica. Sin implementación todavía.

## Documentación

- [Plan técnico](docs/PLAN-TECNICO.md) — arquitectura, elección de plataforma,
  sincronizador multi-proveedor, cumplimiento normativo (UE/España), fases y costes.

## Puntos críticos a resolver antes de empezar

1. **Gases fluorados** — la normativa UE condiciona cómo se puede vender online.
   Ver sección 7.1 del plan técnico.
2. **Modelo de instalación** — propia, red de colaboradores o marketplace.
3. **Formato de catálogo de cada proveedor** — Excel inicialmente, API como objetivo.
