# 13. Anexos

## 13.1 Glosario argentino para los socios españoles

| Término | Traducción al «español de España» |
|---|---|
| **ARCA** | La Agencia Tributaria argentina (ex AFIP). Administra impuestos nacionales, aduana y seguridad social |
| **CUIT** | Clave Única de Identificación Tributaria — el NIF argentino (empresas y personas) |
| **CDI** | Antigua Clave de Identificación para no residentes. **Eliminada en 2026**: hoy los no residentes tramitan CUIT [F9] |
| **Clave fiscal** | La Cl@ve/certificado digital para operar con ARCA online (tiene niveles; el 3 es el operativo) |
| **Monotributo** | Régimen simplificado tipo «autónomo con tarifa plana»: una cuota fija mensual reemplaza IVA + Ganancias + aportes, con topes de facturación por categoría |
| **Responsable Inscripto (RI)** | Régimen general de IVA — como una S.L. española estándar que liquida IVA mes a mes |
| **Factura A / B / C** | A: entre inscriptos (IVA discriminado) · B: de RI a consumidor final · C: la que emite un monotributista |
| **CAE** | Código de Autorización Electrónico: sin él, la factura electrónica no existe ante ARCA |
| **IIBB / Ingresos Brutos** | Impuesto provincial en cascada sobre la facturación (no existe en España). Cada provincia tiene el suyo |
| **Convenio Multilateral (CM)** | Mecanismo para repartir IIBB cuando se opera en varias jurisdicciones (nuestro caso: CABA + PBA) |
| **SIRCREB / SIRCUPA / SIRTAC** | Regímenes que retienen IIBB automáticamente en cuentas bancarias / billeteras / tarjetas — el «goteo» |
| **TISH / tasa municipal** | Tasa de inspección de seguridad e higiene: el «IAE municipal», ligado a tener local |
| **ART** | Aseguradora de Riesgos del Trabajo: la mutua de accidentes laborales, obligatoria con empleados |
| **AP** | Seguro de Accidentes Personales — lo que se le exige a un subcontratado sin ART |
| **Cláusula de no repetición** | La aseguradora renuncia a reclamar contra el contratante: la piden todos los countries |
| **Aguinaldo (SAC)** | Paga extra: un sueldo más al año, en dos mitades (junio y diciembre) |
| **UOM / UOCRA / Comercio** | Sindicatos/convenios: metalúrgicos (incluye refrigeración), construcción y comercio |
| **Autónomos** | Régimen previsional obligatorio de directores/gerentes de sociedades (además del monotributo personal, si lo hay) |
| **SAS / SRL** | SAS ≈ S.L. exprés y flexible; SRL ≈ S.L. clásica |
| **IGJ / DPPJ** | Registros mercantiles de CABA y de la Provincia de Buenos Aires |
| **ARBA / AGIP** | Haciendas de la Provincia de Buenos Aires y de la Ciudad |
| **MiPyME (certificado)** | Sello oficial de pyme: desbloquea beneficios fiscales y financiación (sección 7.7) |
| **Cuotas MiPyME** | Programa privado de cuotas sin interés para el cliente con tasa subsidiada al comercio (sucesor del estatal «Cuota Simple») |
| **MULC / MEP / blue** | Mercado oficial de cambios / dólar bolsa (legal, vía bonos) / mercado informal (descartado) |
| **Nordelta / country / barrio cerrado** | Urbanizaciones privadas con control de acceso — el segmento objetivo premium |
| **AVN** | Asociación Vecinal Nordelta: administra la ciudad-pueblo y el registro de proveedores |
| **Frigoría** | Unidad de frío usada en Argentina (1 frigoría = 1 kcal/h; 3.000 frigorías ≈ 12.000 BTU ≈ 3,5 kW) |

## 13.2 Documentos a preparar en España (checklist de Pedro y Sebastián)

1. Pasaporte vigente (escaneo color, todas las hojas con datos).
2. Certificado de residencia fiscal española (AEAT) — para el CUIT de no residente y para aplicar el CDI a los dividendos.
3. Poder especial notarial + apostilla de La Haya (borrador previamente visado por el escribano argentino).
4. Term sheet del pacto de socios firmado.
5. Justificante del origen de los € 5.000 (extracto) — lo pedirá el compliance bancario argentino.
6. Datos completos: domicilio, estado civil, profesión, email para notificaciones.

## 13.3 Enlaces y contactos oficiales

| Organismo / recurso | URL |
|---|---|
| ARCA (impuestos, CUIT, monotributo) | https://www.arca.gob.ar |
| IGJ — trámites societarios CABA | https://www.argentina.gob.ar/justicia/igj |
| INPI — marcas | https://portaltramites.inpi.gob.ar |
| ARBA (IIBB PBA) | https://www.arba.gov.ar |
| AGIP (IIBB CABA) | https://www.agip.gob.ar |
| Convenio Multilateral (SIFERE) | https://www.ca.gob.ar |
| Registro MiPyME | https://www.argentina.gob.ar/produccion/registrar-una-pyme |
| NIC.ar (dominios) | https://nic.ar |
| AVN Nordelta — proveedores | https://www.avnordelta.com |
| BCRA (régimen cambiario) | https://www.bcra.gob.ar |
| Boletín Oficial | https://www.boletinoficial.gob.ar |

## 13.4 Fuentes citadas (con fecha de consulta)

Las 14 cifras más sensibles del documento (TC, IVA, dividendos, escala de Ganancias, costos SAS, alícuotas IIBB, topes de monotributo, comisiones de cobro, impuestos sobre SaaS, costo laboral, dominios y escala UOM) fueron además contrastadas contra fuentes primarias en una pasada de verificación independiente el 01-08-2026: 11 confirmadas, 3 con matices incorporados al texto y 1 corregida (tasas de Cuotas MiPyME). Convención: [Fn] en el texto → fila de esta tabla. Tipos: oficial (organismo), profesional (estudios/portales especializados), comercial (proveedor), prensa, mercado.

{{tabla_fuentes}}

## 13.5 Cómo se regenera este documento

Este PDF se genera desde el repositorio `nodo-cb`: un archivo Markdown por sección (`src/`), los números centralizados en `src/datos.json` (tipo de cambio, presupuesto, cronograma, stack — los totales y conversiones los calcula el build, no la mano) y las fuentes en `src/fuentes.json`. Para actualizar cifras: editar los JSON y ejecutar `npm run build`. El repositorio incluye además la web completa (`web/`) y el kit digital (`kit-digital/`).

El modelo financiero de la sección 6 tiene una pieza extra: `build/financiero.mjs`, el motor de cálculo que produce **tanto las tablas del PDF como la planilla** `Modelo-Financiero-Clima-Baires-Argentina_v{{meta.version}}.xlsx` (`npm run modelo`). Documento y planilla leen los mismos supuestos de `src/datos.json` y el mismo código, de modo que no pueden contar historias distintas; la hoja «Verificación» de la planilla lo comprueba celda a celda. `npm run todo` regenera los dos de una vez.

El build aborta —no genera un PDF a medias— si queda un marcador `{{ … }}` sin resolver, si se cita una fuente `[Fn]` que no está en `fuentes.json`, si el presupuesto supera los {{eur:capital.total_eur}} o si falta el tipo de cambio. Es deliberado: un documento que se usa para decidir no debería poder publicarse con un hueco.
