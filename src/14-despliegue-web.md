# 14. Puesta en producción de la web

La web está terminada; lo que falta es comprarla, publicarla y conectarla. Todo lo de esta sección se hace en la **semana 1** y cuesta menos de € 40 al año.

## 14.1 Dominios

| Dominio | Dónde | Costo (08-2026) | Notas |
|---|---|---|---|
| **climabaires.com** | Cloudflare Registrar, o cualquier registrador | ≈ USD 10-15/año | El principal del sitio |
| **climabaires.com.ar** | [nic.ar](https://nic.ar) | $ 8.500 de alta + $ 8.500/año [F22] | Exige CUIT y clave fiscal nivel 2 |

El `.com.ar` **no es opcional y no puede esperar**. Argentina otorga la marca y el dominio por orden de llegada, y ya existe un «Clima Baires» informal operando en el GBA sur (riesgo R-02 de la sección 11). Registrarlo cuesta el equivalente a € 10 y cierra la puerta; recuperarlo después de que lo tome otro cuesta un juicio. Se redirige al `.com` con una redirección permanente y no se usa para nada más.

Como el `.com.ar` pide CUIT, la secuencia obliga: **primero el CUIT de la SAS, después el dominio**. Mientras tanto se compra el `.com`, que no pide nada, y se publica el sitio ahí.

## 14.2 Los cinco datos que faltan antes de publicar

La web tiene **un solo punto de configuración** y hoy tiene cinco huecos. Ninguno es trabajo de programación: son datos que aparecen al dar de alta las cuentas de la sección 15.

| Dato | De dónde sale | Si falta |
|---|---|---|
| **Número de WhatsApp** | Chip comercial argentino (15.1) | **Bloqueante.** Hoy hay un número de mentira |
| **Casilla de email** | Google Workspace (15.3) | El formulario y el pie apuntan a una casilla que rebota |
| **Perfiles de Instagram y LinkedIn** | Kit digital (sección 16) | Los iconos del pie no llevan a ningún lado |
| **Identificador de Tag Manager** | Contenedor gratuito de GTM (13.5) | No se mide nada: la pauta se vuelve ciega |
| **Enlace de la agenda** | Página de reservas de Calendar | Los botones «Agendar» derivan a WhatsApp — funciona igual, pero se pierde la cita automática |

Que el número de WhatsApp sea bloqueante no es una formalidad: **el propio comando de publicación se niega a armar el paquete** si detecta los datos de prueba. Publicar el sitio con un número inexistente dejaría todos los botones —que son la única conversión del negocio— apuntando al vacío, y encima gastando pauta. Se puede forzar para una demo, pero no para producción.

## 14.3 Publicar

Lo que se sube **no es la carpeta del proyecto**: pesa unos 40 MB porque incluye las fotos en bruto con sus metadatos, las capturas de control de calidad y los scripts. Publicarlas dejaría material privado accesible por URL. Un comando arma el paquete liviano —unos 5 MB, solo lo que el navegador necesita— y le agrega la configuración de caché y la redirección de `www`.

Tres opciones, las tres gratuitas y con certificado SSL incluido:

1. **Cloudflare Pages** — la recomendada: CDN, SSL y dominio en un mismo panel; si el dominio ya está en Cloudflare, la configuración de DNS se resuelve sola.
2. **Netlify** — se arrastra la carpeta del paquete a su página de despliegue y se añade el dominio.
3. **GitHub Pages** — sirviendo el resultado del empaquetado, con dominio propio y HTTPS forzado.

En cualquiera de las tres: apuntar también `www` y comprobar que el mapa del sitio responda.

## 14.4 Después de publicar

1. **Google Search Console** — dar de alta el dominio y enviar el mapa del sitio. Es lo que hace que Google encuentre las 21 páginas en días en lugar de semanas, y es gratis.
2. **Google Business Profile** — el perfil de empresa (sección 15.2). Para las búsquedas locales pesa más que la web.
3. **Medición** — crear el contenedor de Tag Manager, cargar los eventos de 13.5, marcar las conversiones en GA4 e importarlas en Google Ads bajo la cuenta de la MCC de Málaga. Sin este paso la pauta de diciembre se decide a ciegas.
4. **Vincular GA4 con Ads** para que cada peso invertido quede atribuido a chats y citas.

> **Orden de dependencias.** Dominio → Workspace (necesita el dominio) → WhatsApp (necesita el chip) → publicar la web (necesita el número) → Google Business Profile (necesita la web publicada) → medición → pauta. Saltarse el orden obliga a rehacer pasos: es el mismo encadenamiento que refleja el cronograma de la sección 4.
