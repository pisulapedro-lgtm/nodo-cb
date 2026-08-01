# Google Workspace — guía de alta

**Plan:** Business Starter — **US$7/usuario/mes** (compromiso anual, precio 08-2026). Pagado con tarjeta argentina suma ~53-56% de impuestos (IVA 21% + percepción Ganancias 30% + IIBB) → presupuestar **≈ US$11/usuario/mes efectivos**. La percepción del 30% es a cuenta de Ganancias/Bienes Personales: el contador la recupera en la DDJJ. [Detalle en el PDF, sección stack]

## 1. Alta
1. Ir a [workspace.google.com](https://workspace.google.com) → *Empezar prueba gratuita* (14 días).
2. Nombre de empresa: Clima Baires Argentina · Empleados: 2-9 · País: Argentina.
3. «¿Tenés dominio?» → **Sí, climabaires.com** (comprarlo antes: ver web/README.md).
4. Usuario administrador: **ignacio@climabaires.com**.

## 2. Verificación del dominio y correo (DNS)
En el panel DNS del registrador (o Cloudflare si se usó Cloudflare Pages):
| Tipo | Nombre | Valor | Para |
|---|---|---|---|
| TXT | @ | `google-site-verification=XXXX` (lo da el asistente) | Verificar dominio |
| MX | @ | `smtp.google.com` (prioridad 1) | Recibir correo |
| TXT | @ | `v=spf1 include:_spf.google.com ~all` | SPF (antispam) |
| TXT | `google._domainkey` | (generar en Admin → Apps → Google Workspace → Gmail → Autenticar) | DKIM |
| TXT | `_dmarc` | `v=DMARC1; p=quarantine; rua=mailto:ignacio@climabaires.com` | DMARC |
Verificar todo en [admin.google.com](https://admin.google.com) → el asistente marca cada paso en verde.

## 3. Usuarios y grupos (estructura mínima = 1-2 licencias pagas)
| Dirección | Tipo | Notas |
|---|---|---|
| ignacio@climabaires.com | Usuario | Admin. Único usuario pago imprescindible al inicio |
| redes@climabaires.com | Usuario (opcional) | Si se quiere separar redes/marketing; si no, alias de ignacio@ |
| info@ · presupuestos@ · posventa@ | **Grupos** (gratis) | Entregan a ignacio@; el día que haya administrativo, se lo suma al grupo sin migrar nada |
| pedro@ / sebastian@ | **Alias o grupo** hacia sus emails personales | Los socios remotos no necesitan licencia paga para recibir |

## 4. Configuración recomendada semana 1
- **Calendar:** calendario compartido «Instalaciones» (agenda de obra: técnico, dirección, equipo, estado) — es el field service lean del arranque.
- **Drive compartido** «Clima Baires Ops»: carpetas `Presupuestos / Obras (fotos checklist) / Proveedores / Fiscal`.
- **Forms:** «Checklist de instalación» (fotos + firma del cliente en obra desde el celular del instalador) — plantilla descrita en el PDF, sección operaciones.
- 2FA obligatoria para todos los usuarios (Admin → Seguridad).
