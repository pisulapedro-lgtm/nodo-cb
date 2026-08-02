/* Clima Baires — climabaires.es
   Configuración central de contacto y medición: EDITAR SOLO AQUÍ.
   - whatsapp: placeholder hasta el alta de la línea española (web-es/README.md → "Antes de publicar").
   - gtmId: contenedor de Google Tag Manager (GTM-XXXXXXX = placeholder → no se carga nada).
     OJO: el contenedor argentino no sirve, son propiedades distintas.
   - agendaUrl: página de reservas de Google Calendar
     (placeholder vacío → los botones "Agendar visita" derivan a WhatsApp).
   - placeId: Place ID de la ficha de Google Business Profile. Alimenta el mapa
     de contacto.html y los enlaces de reseñas. Vacío → no hay mapa ni enlaces.
   - mapsKey: clave de Maps Embed API (opcional). Sin clave se usa el embed
     clásico, que funciona igual pero no está cubierto por el contrato de la API. */
const CB = {
  whatsapp: '34600000000',              // formato internacional sin '+' (34 6XX XXX XXX)
  whatsappVisible: '+34 600 00 00 00',
  email: 'info@climabaires.es',
  horario: 'De lunes a sábado, de 8:00 a 19:00',
  instagram: '',                        // vacío → el pie no muestra el enlace
  linkedin: '',
  gtmId: 'GTM-XXXXXXX',                 // ID del contenedor GTM (único punto de configuración)
  agendaUrl: '',                        // URL de la agenda de citas de Google Calendar
  placeId: '',                          // Place ID de Google Business Profile
  mapsKey: '',                          // clave de Maps Embed API (opcional)
};

window.CB_NUM = CB.whatsapp;

function cbMensaje(txt) {
  return 'https://wa.me/' + CB.whatsapp + '?text=' + encodeURIComponent(txt || 'Hola Clima Baires, quiero pedir presupuesto.');
}

/* ---------- Medición: todo clic empuja un evento al dataLayer ----------
   GTM lee estos eventos (spec completa en web-es/README.md). El dataLayer existe
   siempre (lo inicializa el <head>): si GTM aún no cargó, los eventos quedan
   encolados y se procesan al cargar. */
function cbTrack(evento, params) {
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push(Object.assign({ event: evento }, params || {}));
}

function cbContexto(el) {
  const b = document.body;
  return {
    origen: (el && el.dataset.origen) || 'seccion',
    pagina: b.dataset.pagina || location.pathname.split('/').pop() || 'index',
    zona: b.dataset.zona || '',
  };
}

/* ---------- Consentimiento de cookies (RGPD + LSSI-CE art. 22.2) ----------
   En España nada que no sea estrictamente necesario puede cargarse antes de que
   el usuario diga que sí: ni GTM, ni el mapa de Google, ni el iframe de la
   agenda. Por eso el consentimiento no es un aviso decorativo: es la llave que
   abre esas tres cargas. Rechazar cuesta lo mismo que aceptar —dos botones al
   mismo nivel, sin muro que tape el sitio—, que es justo lo que exige la guía
   de la AEPD.

   El estado vive en localStorage. En file:// (el QA de Playwright abre así) el
   navegador puede negar el acceso, de modo que hay una copia en memoria: el
   banner sigue funcionando y la decisión dura lo que dura la página. */
const CB_COOKIES_CLAVE = 'cb-cookies';
let cbDecisionMemoria = null;
const cbPendientes = [];

function cbDecision() {
  try {
    const v = localStorage.getItem(CB_COOKIES_CLAVE);
    if (v) return v;
  } catch (e) { /* file:// o almacenamiento bloqueado: se usa la copia en memoria */ }
  return cbDecisionMemoria;
}

function cbGuardarDecision(valor) {
  cbDecisionMemoria = valor;
  try { localStorage.setItem(CB_COOKIES_CLAVE, valor); } catch (e) { /* ídem */ }
}

/** Ejecuta `fn` cuando haya consentimiento; si ya lo hay, ahora mismo. */
function cbAlAceptar(fn) {
  if (cbDecision() === 'aceptado') fn();
  else cbPendientes.push(fn);
}

/* Consent Mode v2: los valores por defecto se declaran ANTES de que exista GTM,
   así el contenedor —si está configurado con consentimiento— nunca arranca con
   permisos que el usuario no ha dado. Al aceptar se manda el update. */
function cbGtag() { (window.dataLayer = window.dataLayer || []).push(arguments); }

cbGtag('consent', 'default', {
  ad_storage: 'denied',
  ad_user_data: 'denied',
  ad_personalization: 'denied',
  analytics_storage: 'denied',
  functionality_storage: 'denied',
  personalization_storage: 'denied',
  security_storage: 'granted',
  wait_for_update: 500,
});

/* GTM: única puerta de medición (GA4, Ads y Meta se cargan DESDE el contenedor).
   Con el placeholder no se inyecta nada; sin consentimiento, tampoco. */
function cbCargarGTM() {
  if (!CB.gtmId || /XXXXXXX$/.test(CB.gtmId) || window.google_tag_manager) return;
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
  const s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtm.js?id=' + CB.gtmId;
  document.head.appendChild(s);
}

function cbAceptarCookies() {
  cbGuardarDecision('aceptado');
  cbGtag('consent', 'update', {
    ad_storage: 'granted',
    ad_user_data: 'granted',
    ad_personalization: 'granted',
    analytics_storage: 'granted',
    functionality_storage: 'granted',
    personalization_storage: 'granted',
  });
  cbCargarGTM();
  cbTrack('cookies_consentimiento', { decision: 'aceptado' });
  while (cbPendientes.length) cbPendientes.shift()();
}

function cbRechazarCookies() {
  cbGuardarDecision('rechazado');
  cbTrack('cookies_consentimiento', { decision: 'rechazado' });
  cbPendientes.length = 0;
}

if (cbDecision() === 'aceptado') cbCargarGTM();   // no espera al DOMContentLoaded

document.addEventListener('DOMContentLoaded', () => {
  const agendaActiva = /^https:/.test(CB.agendaUrl);

  // ---------- Banner de consentimiento ----------
  const banner = document.getElementById('cookies');
  if (banner) {
    const cerrar = () => {
      banner.hidden = true;
      document.body.classList.remove('cookies-abierto');
    };
    const abrir = () => {
      banner.hidden = false;
      document.body.classList.add('cookies-abierto');
    };
    banner.querySelector('.ck-aceptar').addEventListener('click', () => { cbAceptarCookies(); cerrar(); });
    banner.querySelector('.ck-rechazar').addEventListener('click', () => { cbRechazarCookies(); cerrar(); });
    if (!cbDecision()) abrir();
    // «Preferencias de cookies», en el pie: vuelve a preguntar. Es el único modo
    // de retirar un consentimiento ya dado sin vaciar el navegador entero.
    document.querySelectorAll('[data-cookies-abrir]').forEach((b) => {
      b.addEventListener('click', (e) => {
        e.preventDefault();
        try { localStorage.removeItem(CB_COOKIES_CLAVE); } catch (err) { /* ídem */ }
        cbDecisionMemoria = null;
        abrir();
        banner.querySelector('.ck-aceptar').focus();
      });
    });
  }

  // Enlaces y textos de contacto. Los CTA abren WhatsApp en otra pestaña: así el
  // documento no se descarga y el evento de conversión llega a salir.
  document.querySelectorAll('[data-wsp]').forEach((a) => {
    a.href = cbMensaje(a.dataset.wsp);
    if (a.tagName === 'A') { a.target = '_blank'; a.rel = 'noopener'; }
    // Los que abren el asistente (data-chat) no cuentan como whatsapp_click aquí:
    // el clic no sale a WhatsApp todavía. Miden chatbot_inicio al abrirse y
    // whatsapp_click sólo cuando el usuario pulsa «Continuar en WhatsApp».
    if (a.hasAttribute('data-chat')) return;
    a.addEventListener('click', () => cbTrack('whatsapp_click', cbContexto(a)));
  });
  document.querySelectorAll('[data-wsp-num]').forEach((el) => { el.textContent = CB.whatsappVisible; });
  document.querySelectorAll('[data-email]').forEach((el) => {
    const ctx = cbContexto(el);
    const asunto = 'Presupuesto — ' + (ctx.zona || 'climabaires.es');
    el.textContent = CB.email;
    el.href = 'mailto:' + CB.email + '?subject=' + encodeURIComponent(asunto);
  });
  document.querySelectorAll('[data-horario]').forEach((el) => { el.textContent = CB.horario; });
  document.querySelectorAll('[data-ig]').forEach((el) => { if (CB.instagram) el.href = CB.instagram; });
  document.querySelectorAll('[data-li]').forEach((el) => { if (CB.linkedin) el.href = CB.linkedin; });

  // Agenda de visitas (Google Calendar): con el placeholder deriva a WhatsApp
  document.querySelectorAll('[data-agenda]').forEach((a) => {
    if (agendaActiva) {
      a.href = CB.agendaUrl;
      a.target = '_blank';
      a.rel = 'noopener';
    } else {
      a.href = cbMensaje('Hola Clima Baires, quiero concertar una visita técnica.');
    }
    a.addEventListener('click', () => cbTrack('agenda_click', cbContexto(a)));
  });

  // Iframe de reservas en contacto.html. Es una carga de Google: no entra sin
  // consentimiento. Si no lo hay queda el botón, que abre la agenda en otra
  // pestaña — eso lo decide el usuario y no necesita permiso previo.
  const embed = document.querySelector('[data-agenda-embed]');
  if (embed && agendaActiva) {
    const montar = () => {
      const f = document.createElement('iframe');
      f.src = CB.agendaUrl;
      f.title = 'Reservar visita técnica — Google Calendar';
      f.loading = 'lazy';
      f.className = 'agenda-iframe';
      embed.appendChild(f);
    };
    cbAlAceptar(() => {
      ('requestIdleCallback' in window) ? requestIdleCallback(montar, { timeout: 4000 }) : setTimeout(montar, 1500);
    });
  }

  // Mapa de la ficha de Google: sólo en contacto.html y sólo con consentimiento.
  // Es la tercera carga externa del sitio y va diferida, así que nunca compite
  // con el LCP de la portada.
  const mapa = document.querySelector('[data-mapa-embed]');
  if (mapa && CB.placeId) {
    const src = CB.mapsKey
      ? 'https://www.google.com/maps/embed/v1/place?key=' + encodeURIComponent(CB.mapsKey) +
        '&q=place_id:' + encodeURIComponent(CB.placeId) + '&language=es&region=ES'
      : 'https://www.google.com/maps?q=place_id:' + encodeURIComponent(CB.placeId) + '&hl=es&output=embed';
    const montar = () => {
      const f = document.createElement('iframe');
      f.src = src;
      f.title = 'Ubicación de Clima Baires en Google Maps';
      f.loading = 'lazy';
      f.referrerPolicy = 'no-referrer-when-downgrade';
      f.className = 'mapa-iframe';
      mapa.appendChild(f);
      const aviso = mapa.querySelector('.mapa-sin-consentimiento');
      if (aviso) aviso.hidden = true;
    };
    cbAlAceptar(() => {
      ('requestIdleCallback' in window) ? requestIdleCallback(montar, { timeout: 4000 }) : setTimeout(montar, 1500);
    });
  }

  // Clics medidos en teléfono, email y reseñas escritos a mano en el contenido
  document.querySelectorAll('a[href^="tel:"]').forEach((a) => {
    a.addEventListener('click', () => cbTrack('tel_click', { pagina: cbContexto(a).pagina }));
  });
  document.querySelectorAll('a[href^="mailto:"], [data-email]').forEach((a) => {
    a.addEventListener('click', () => cbTrack('email_click', { pagina: cbContexto(a).pagina }));
  });
  document.querySelectorAll('[data-resena]').forEach((a) => {
    a.addEventListener('click', () => cbTrack('resenas_click', {
      destino: a.dataset.resena, pagina: cbContexto(a).pagina,
    }));
  });

  // Menú móvil
  const btn = document.querySelector('.hamburguesa');
  const nav = document.querySelector('.nav');
  if (btn && nav) btn.addEventListener('click', () => nav.classList.toggle('abierta'));

  // La promesa de respuesta se ajusta al horario real (de lunes a sábado, de 8:00
  // a 19:00): prometer «en minutos» un domingo de madrugada es una promesa que no
  // se cumple.
  const ahora = new Date();
  const enHorario = ahora.getDay() !== 0 && ahora.getHours() >= 8 && ahora.getHours() < 19;
  if (!enHorario) {
    document.querySelectorAll('[data-respuesta]').forEach((el) => {
      el.textContent = 'Te respondemos al abrir: de lunes a sábado, de 8:00 a 19:00';
    });
  }

  // Año en el pie
  document.querySelectorAll('[data-anio]').forEach((el) => { el.textContent = new Date().getFullYear(); });

  // Barra inferior móvil: se oculta mientras el teclado está abierto
  const barra = document.querySelector('.barra-movil');
  if (barra) {
    document.addEventListener('focusin', (e) => {
      if (e.target.matches('input, textarea, select')) barra.classList.add('oculta');
    });
    document.addEventListener('focusout', () => setTimeout(() => barra.classList.remove('oculta'), 150));
  }

  // Chatbot: 4 preguntas (nombre, zona, servicio, tipo de aire) → WhatsApp
  const chat = document.getElementById('chat');
  const flotante = document.querySelector('.wsp-flotante');
  if (chat && flotante) {
    const mensajes = document.getElementById('chat-mensajes');
    const pie = document.getElementById('chat-pie');
    const r = { nombre: '', zona: '', servicio: '', tipo: '' };
    let iniciado = false;

    const burbuja = (texto, mia) => {
      const b = document.createElement('div');
      b.className = 'burbuja' + (mia ? ' mia' : '');
      b.textContent = texto;
      mensajes.appendChild(b);
      mensajes.scrollTop = mensajes.scrollHeight;
    };

    const chips = (opciones, alElegir) => {
      pie.innerHTML = '';
      opciones.forEach((op) => {
        const c = document.createElement('button');
        c.type = 'button';
        c.className = 'chat-chip';
        c.dataset.valor = op;
        c.textContent = op;
        c.addEventListener('click', () => { burbuja(op, true); alElegir(op); });
        pie.appendChild(c);
      });
    };

    const entradaNombre = (alEnviar) => {
      pie.innerHTML = '';
      const form = document.createElement('form');
      form.className = 'chat-form';
      form.innerHTML = '<input name="nombre" placeholder="Tu nombre" autocomplete="given-name" maxlength="40" required>' +
                       '<button class="boton" type="submit">Enviar</button>';
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const v = form.nombre.value.trim().slice(0, 40);
        if (!v) return;
        burbuja(v, true);
        alEnviar(v);
      });
      pie.appendChild(form);
      form.nombre.focus();
    };

    const paso2 = () => {
      burbuja('¿Dónde vives?');
      cbTrack('chatbot_paso', { paso: 1, pagina: cbContexto(chat).pagina });
      const zonas = ['Málaga capital', 'Marbella', 'Torremolinos', 'Benalmádena', 'Fuengirola', 'Mijas', 'Otra zona'];
      const propia = document.body.dataset.zona;
      if (propia && zonas.includes(propia)) zonas.splice(zonas.indexOf(propia), 1) && zonas.unshift(propia);
      chips(zonas, (z) => { r.zona = z; paso3(); });
    };
    const paso3 = () => {
      burbuja('¿Qué servicio buscas?');
      cbTrack('chatbot_paso', { paso: 2, respuesta: r.zona, pagina: cbContexto(chat).pagina });
      chips(['Instalación nueva', 'Sustitución de equipo', 'Mantenimiento y limpieza', 'Reparación'], (s) => { r.servicio = s; paso4(); });
    };
    const paso4 = () => {
      burbuja('¿Qué tipo de aire acondicionado?');
      cbTrack('chatbot_paso', { paso: 3, respuesta: r.servicio, pagina: cbContexto(chat).pagina });
      chips(['Split', 'Multisplit', 'Suelo-techo', 'Cassette o conductos', 'No lo sé, necesito asesoramiento'], (t) => { r.tipo = t; cierre(); });
    };
    const cierre = () => {
      cbTrack('chatbot_paso', { paso: 4, respuesta: r.tipo, pagina: cbContexto(chat).pagina });
      burbuja('Listo, ' + r.nombre + '. Pulsa el botón y seguimos por WhatsApp con tu consulta ya preparada. Respondemos en minutos.');
      const msj = 'Hola, soy ' + r.nombre + ' y vivo en ' + r.zona + '. Busco: ' + r.servicio +
                  '. Tipo de aire: ' + r.tipo + '.';
      pie.innerHTML = '';
      const a = document.createElement('a');
      a.className = 'boton chat-final';
      a.href = cbMensaje(msj);
      a.target = '_blank';
      a.rel = 'noopener';
      a.textContent = 'Continuar en WhatsApp';
      a.addEventListener('click', () => cbTrack('whatsapp_click', {
        origen: 'chatbot', pagina: cbContexto(chat).pagina, zona: r.zona,
      }));
      pie.appendChild(a);
      a.focus();
    };

    const abrir = () => {
      chat.hidden = false;
      flotante.classList.add('abierto');
      if (!iniciado) {
        iniciado = true;
        cbTrack('chatbot_inicio', { pagina: cbContexto(chat).pagina });
        burbuja('Hola ❄ Soy el asistente de Clima Baires. Cuatro preguntas y seguimos por WhatsApp.');
        burbuja('¿Cómo te llamas?');
        entradaNombre((v) => { r.nombre = v; paso2(); });
      } else if (pie.querySelector('input')) {
        pie.querySelector('input').focus();
      }
    };
    const cerrar = () => { chat.hidden = true; flotante.classList.remove('abierto'); };

    flotante.addEventListener('click', () => (chat.hidden ? abrir() : cerrar()));

    // Los CTA fijos que acompañan todo el scroll entran por el asistente: cuatro
    // preguntas y el mensaje sale con nombre, zona, servicio y tipo de equipo.
    // Los CTA de contenido (hero, cintas, tarjetas) siguen yendo directos, porque
    // cada uno ya lleva su propio mensaje con el contexto de dónde se pulsó.
    // El href a wa.me se deja puesto: si el JS no ha cargado, el botón sirve igual.
    document.querySelectorAll('[data-chat]').forEach((a) => {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        // abrir() sirve para los dos casos: si el chat ya estaba abierto,
        // devuelve el foco a la pregunta en curso. Sin esto, pulsar el botón de
        // la barra con el asistente abierto no hacía nada y se leía como roto.
        abrir();
      });
    });
    chat.querySelector('.chat-cerrar').addEventListener('click', cerrar);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !chat.hidden) cerrar();
    });
  }

  // Nudge del botón flotante: una sola vez por sesión, a los 20 s o al 50% de scroll
  const nudge = document.getElementById('nudge');
  if (nudge && !sessionStorage.getItem('cbNudge')) {
    let mostrado = false;
    const mostrar = () => {
      if (mostrado) return;
      mostrado = true;
      try { sessionStorage.setItem('cbNudge', '1'); } catch (e) { /* file:// */ }
      nudge.hidden = false;
    };
    const timer = setTimeout(mostrar, 20000);
    const alScroll = () => {
      const total = document.documentElement.scrollHeight - innerHeight;
      if (total > 0 && scrollY / total >= 0.5) { mostrar(); removeEventListener('scroll', alScroll); }
    };
    addEventListener('scroll', alScroll, { passive: true });
    nudge.querySelector('.nudge-cerrar').addEventListener('click', () => {
      nudge.hidden = true;
      clearTimeout(timer);
    });
    nudge.querySelector('.nudge-texto').addEventListener('click', () => {
      nudge.hidden = true;
      document.querySelector('.wsp-flotante').click();
    });
  }

  // Calculadora de frigorías
  const form = document.getElementById('calc-frigorias');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const m2 = parseFloat(form.m2.value);
      const altura = parseFloat(form.altura.value);
      const orientacion = form.orientacion.value;
      const ventanales = form.ventanales.value === 'si';
      const personas = parseInt(form.personas.value, 10);
      if (!m2 || m2 <= 0) return;

      // Base: 100 frigorías/m² con techo estándar de 2,6 m, corregida por el
      // volumen real. Estamos en el hemisferio norte: aquí la fachada que se
      // lleva el sol todo el día es la SUR, y la de poniente, el golpe de calor
      // de la tarde. (En el sitio argentino esos coeficientes van al revés.)
      let frig = m2 * 100 * (altura / 2.6);
      if (orientacion === 'sur') frig *= 1.10;
      if (orientacion === 'oeste') frig *= 1.15;
      if (ventanales) frig *= 1.10;
      if (personas > 2) frig += (personas - 2) * 300;

      // Escalera comercial española: los equipos se venden por BTU, así que cada
      // escalón lleva su equivalencia (1 frigoría/h ≈ 3,97 BTU/h).
      const comerciales = [2250, 3000, 4500, 6000, 7500, 9000, 12000, 15000, 18000];
      const btu = { 2250: 9000, 3000: 12000, 4500: 18000, 6000: 24000, 7500: 30000,
                    9000: 36000, 12000: 48000, 15000: 60000, 18000: 72000 };
      const rec = comerciales.find((c) => c >= frig) || comerciales[comerciales.length - 1];

      const res = document.getElementById('calc-resultado');
      res.classList.add('visible');
      res.querySelector('.cifra').textContent =
        Math.round(frig).toLocaleString('es-ES') + ' frigorías · ' +
        (Math.round(frig * 3.968 / 100) * 100).toLocaleString('es-ES') + ' BTU';
      res.querySelector('.equipo').textContent =
        'Equipo recomendado: split de ' + rec.toLocaleString('es-ES') + ' frigorías (' +
        btu[rec].toLocaleString('es-ES') + ' BTU)' +
        (rec >= 15000 ? ', o suelo-techo y conductos: lo definimos en la visita' : '');
      const wsp = res.querySelector('a[data-wsp-calc]');
      wsp.href = cbMensaje(
        'Hola Clima Baires. He usado la calculadora: estancia de ' + m2 + ' m², resultado ' +
        Math.round(frig) + ' frigorías. ¿Me pasáis presupuesto de equipo más instalación?'
      );
      cbTrack('calculadora_uso', {
        m2: m2,
        frigorias_resultado: Math.round(frig),
        equipo_recomendado: rec,
        pagina: 'calculadora-frigorias',
      });
    });
    const wspCalc = form.querySelector('a[data-wsp-calc]');
    if (wspCalc) wspCalc.addEventListener('click', () => cbTrack('whatsapp_click', {
      origen: 'calculadora', pagina: 'calculadora-frigorias', zona: '',
    }));
  }

  // Formulario de contacto → deriva a WhatsApp (sin backend) y mide el envío
  const fc = document.getElementById('form-contacto');
  if (fc) {
    fc.addEventListener('submit', (e) => {
      e.preventDefault();
      const txt = 'Hola Clima Baires, soy ' + fc.nombre.value + ' (' + fc.zona.value + '). ' + fc.mensaje.value;
      cbTrack('form_envio', { zona: fc.zona.value, pagina: cbContexto(fc).pagina });
      window.open(cbMensaje(txt), '_blank');
    });
  }

  // Carrusel de obras en la portada: flechas de desplazamiento
  const carrusel = document.getElementById('obras-carrusel');
  if (carrusel) {
    const paso = () => Math.min(carrusel.clientWidth * 0.8, 700);
    const prev = document.querySelector('.car-prev');
    const next = document.querySelector('.car-next');
    if (prev) prev.addEventListener('click', () => carrusel.scrollBy({ left: -paso(), behavior: 'smooth' }));
    if (next) next.addEventListener('click', () => carrusel.scrollBy({ left: paso(), behavior: 'smooth' }));
  }

  // Blog: filtro por tema (mismo patrón que la galería, sin lightbox)
  const grillaPosts = document.getElementById('post-grilla');
  if (grillaPosts) {
    const posts = Array.from(grillaPosts.querySelectorAll('.post-tarjeta'));
    document.querySelectorAll('.filtro[data-grupo="cat"]').forEach((b) => {
      b.addEventListener('click', () => {
        const v = b.dataset.valor;
        let visibles = 0;
        posts.forEach((p) => {
          const ok = v === 'todas' || p.dataset.categoria === v;
          p.classList.toggle('oculta', !ok);
          if (ok) visibles++;
        });
        document.querySelectorAll('.filtro[data-grupo="cat"]')
          .forEach((o) => o.setAttribute('aria-pressed', o === b ? 'true' : 'false'));
        const vacio = document.getElementById('post-vacio');
        if (vacio) vacio.hidden = visibles > 0;
      });
    });
  }

  // Galería de obras: filtros por zona/tipo + lightbox accesible
  const galeria = document.getElementById('obras-grilla');
  if (galeria) {
    const items = Array.from(galeria.querySelectorAll('.obra'));
    const estado = { zona: 'todas', tipo: 'todos' };

    const aplicar = () => {
      let visibles = 0;
      items.forEach((it) => {
        const ok = (estado.zona === 'todas' || it.dataset.zona === estado.zona) &&
                   (estado.tipo === 'todos' || it.dataset.tipo === estado.tipo);
        it.classList.toggle('oculta', !ok);
        if (ok) visibles++;
      });
      const vacio = document.getElementById('obras-vacio');
      if (vacio) vacio.hidden = visibles > 0;
    };

    document.querySelectorAll('.filtro').forEach((b) => {
      b.addEventListener('click', () => {
        const grupo = b.dataset.grupo;                    // 'zona' | 'tipo'
        estado[grupo] = b.dataset.valor;
        document.querySelectorAll(`.filtro[data-grupo="${grupo}"]`)
          .forEach((o) => o.setAttribute('aria-pressed', o === b ? 'true' : 'false'));
        aplicar();
      });
    });

    // Lightbox
    const lb = document.getElementById('lightbox');
    const lbImg = lb.querySelector('.lb-img');
    const lbCap = lb.querySelector('.lb-cap');
    const lbWsp = lb.querySelector('.lb-wsp');
    let actual = -1;
    let previo = null;

    const visibles = () => items.filter((it) => !it.classList.contains('oculta'));

    const abrir = (item) => {
      const lista = visibles();
      actual = lista.indexOf(item);
      if (actual < 0) return;
      previo = document.activeElement;
      const b = item.querySelector('.obra-abrir');
      lbImg.src = b.dataset.full;
      lbImg.alt = b.dataset.alt;
      lbCap.textContent = b.dataset.alt;
      const msj = 'He visto la obra ' + b.dataset.slug + ' en vuestra web y quiero algo así en casa.';
      lbWsp.dataset.wsp = msj;
      lbWsp.href = cbMensaje(msj);
      lb.hidden = false;
      document.body.style.overflow = 'hidden';
      lb.querySelector('.lb-cerrar').focus();
    };
    const cerrar = () => {
      lb.hidden = true;
      document.body.style.overflow = '';
      if (previo) previo.focus();
    };
    const mover = (paso) => {
      const lista = visibles();
      if (!lista.length) return;
      actual = (actual + paso + lista.length) % lista.length;
      abrir(lista[actual]);
    };

    items.forEach((it) => it.querySelector('.obra-abrir').addEventListener('click', () => abrir(it)));
    lb.querySelector('.lb-cerrar').addEventListener('click', cerrar);
    lb.querySelector('.lb-prev').addEventListener('click', () => mover(-1));
    lb.querySelector('.lb-next').addEventListener('click', () => mover(1));
    lb.addEventListener('click', (e) => { if (e.target === lb) cerrar(); });
    document.addEventListener('keydown', (e) => {
      if (lb.hidden) return;
      if (e.key === 'Escape') cerrar();
      if (e.key === 'ArrowLeft') mover(-1);
      if (e.key === 'ArrowRight') mover(1);
      if (e.key === 'Tab') {                             // foco contenido en el lightbox
        const focos = lb.querySelectorAll('button, a[href]');
        const primero = focos[0], ultimo = focos[focos.length - 1];
        if (e.shiftKey && document.activeElement === primero) { e.preventDefault(); ultimo.focus(); }
        else if (!e.shiftKey && document.activeElement === ultimo) { e.preventDefault(); primero.focus(); }
      }
    });
  }

});
