/* Clima Baires — climabaires.com
   Configuración central de contacto: EDITAR SOLO AQUÍ.
   El número de WhatsApp es un placeholder hasta el alta de la línea argentina
   (ver web/README.md → "Antes de publicar"). */
const CB = {
  whatsapp: '5491100000000',            // formato internacional sin '+' (54 9 11 XXXX XXXX)
  whatsappVisible: '+54 9 11 0000-0000',
  email: 'info@climabaires.com',
  horario: 'Lunes a sábado, 8 a 19 h',
  instagram: 'https://www.instagram.com/climabaires.ar/',
  linkedin: 'https://www.linkedin.com/company/clima-baires-argentina/',
};

window.CB_NUM = CB.whatsapp;

function cbMensaje(txt) {
  return 'https://wa.me/' + CB.whatsapp + '?text=' + encodeURIComponent(txt || 'Hola Clima Baires, quiero pedir un presupuesto.');
}

document.addEventListener('DOMContentLoaded', () => {
  // Enlaces y textos de contacto
  document.querySelectorAll('[data-wsp]').forEach((a) => {
    a.href = cbMensaje(a.dataset.wsp);
  });
  document.querySelectorAll('[data-wsp-num]').forEach((el) => { el.textContent = CB.whatsappVisible; });
  document.querySelectorAll('[data-email]').forEach((el) => {
    el.textContent = CB.email; el.href = 'mailto:' + CB.email;
  });
  document.querySelectorAll('[data-horario]').forEach((el) => { el.textContent = CB.horario; });
  document.querySelectorAll('[data-ig]').forEach((el) => { el.href = CB.instagram; });
  document.querySelectorAll('[data-li]').forEach((el) => { el.href = CB.linkedin; });

  // Menú móvil
  const btn = document.querySelector('.hamburguesa');
  const nav = document.querySelector('.nav');
  if (btn && nav) btn.addEventListener('click', () => nav.classList.toggle('abierta'));

  // Año en el pie
  document.querySelectorAll('[data-anio]').forEach((el) => { el.textContent = new Date().getFullYear(); });

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

      // Base: 100 frigorías/m² con techo estándar 2,6 m, corregida por volumen real
      let frig = m2 * 100 * (altura / 2.6);
      if (orientacion === 'norte') frig *= 1.10;      // sol de tarde-norte (hemisferio sur)
      if (orientacion === 'oeste') frig *= 1.15;
      if (ventanales) frig *= 1.10;
      if (personas > 2) frig += (personas - 2) * 300;

      const comerciales = [2250, 3000, 4500, 5500, 6500, 9000, 12000, 15000, 18000];
      const rec = comerciales.find((c) => c >= frig) || comerciales[comerciales.length - 1];

      const res = document.getElementById('calc-resultado');
      res.classList.add('visible');
      res.querySelector('.cifra').textContent = Math.round(frig).toLocaleString('es-AR') + ' frigorías';
      res.querySelector('.equipo').textContent =
        'Equipo recomendado: split de ' + rec.toLocaleString('es-AR') + ' frigorías' +
        (rec >= 15000 ? ' (o piso-techo / conductos: lo definimos en la visita)' : '');
      const wsp = res.querySelector('a[data-wsp-calc]');
      wsp.href = cbMensaje(
        'Hola Clima Baires. Usé la calculadora: ambiente de ' + m2 + ' m², resultado ' +
        Math.round(frig) + ' frigorías. ¿Me pasan presupuesto de equipo + instalación?'
      );
    });
  }
});
