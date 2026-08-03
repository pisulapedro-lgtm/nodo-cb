# 18. Google Ads — campañas listas para cargar

Esta sección se puede ejecutar sin decidir nada más: la estructura, las palabras clave, las negativas y los textos están escritos. Ignacio abre la cuenta y carga.

**El activo heredado.** Clima Baires España lleva **más de € 16.000 invertidos** en el mismo rubro. Eso no es dinero gastado: es un histórico de qué búsquedas compran y cuáles hacen perder plata, que ningún competidor del corredor tiene. Lo que viaja y lo que no:

| Viaja | No viaja |
|---|---|
| La **estructura** por intención (instalación / recambio / service / urgencia), ya validada | El historial de calidad del anuncio: es por cuenta y país |
| La **lista de negativas** depurada en años — el ahorro más grande de los primeros 90 días | Las audiencias y las conversiones acumuladas |
| Los **textos ganadores**: qué mensaje tiene mejor CTR en este negocio exacto | Los CPC: Argentina es otro mercado y otra puja |
| Los **ratios de referencia** de Málaga como vara para juzgar el rendimiento desde la semana 1 | La estacionalidad: está invertida |

## 18.1 Configuración de la cuenta

1. **Crear la cuenta argentina bajo la misma MCC** que la de Málaga: gobernanza unificada, facturación separada.
2. **Facturación local en ARS** — obligatorio. Pagar desde el exterior suma más de 50 % de impuestos no recuperables contra el 24 % con IVA recuperable de la facturación local [F21]. Es el error más caro que se puede cometer en la configuración inicial.
3. **Idioma**: español. **Ubicación**: los seis municipios por radio, con la opción *«presencia: personas que están habitualmente en la zona»* — no «personas interesadas en la zona», que trae consultas de todo el país.
4. **Conversiones importadas desde GA4**: `whatsapp_click` y `agenda_click` como principales, `calculadora_uso` como secundaria (sección 13.5). Sin esto la campaña optimiza hacia el clic barato en vez de hacia el cliente.
5. **Programación**: de lunes a sábado de 7 a 21. Fuera de horario el lead se enfría antes de que alguien conteste, y el mensaje automático de ausencia no lo salva.
6. **Exclusión de la red de Display y de socios de búsqueda** en todas las campañas de Search. Se activan solo si sobra presupuesto, que no va a pasar.

## 18.2 Estructura de campañas

{{tabla_campanas_google}}

La regla que ordena todo esto: **un grupo de anuncios por intención y por zona, cada uno apuntando a su propia landing**. La búsqueda «instalación aire acondicionado Nordelta» tiene que caer en la página de Nordelta, no en la portada. Es lo que sube el nivel de calidad, y el nivel de calidad es lo que baja el CPC — las páginas de zona de la sección 13 existen exactamente para esto.

## 18.3 Palabras clave

Concordancia de **frase** para lo genérico y **exacta** para lo caro. Nada en concordancia amplia hasta tener 50 conversiones de historial: la amplia con poco historial es una forma elegante de regalar presupuesto.

**Campaña Instalación** — un grupo por municipio, replicando el patrón:

| Grupo | Palabras clave |
|---|---|
| Instalación · genérico | `"instalacion aire acondicionado"` · `"instalar aire acondicionado"` · `"instalacion split"` · `"colocacion aire acondicionado"` · `[instalacion de aire acondicionado precio]` |
| Instalación · Núñez | `"aire acondicionado nuñez"` · `"instalacion aire acondicionado nuñez"` · `"instalador split nuñez"` |
| Instalación · Vicente López | `"aire acondicionado vicente lopez"` · `"instalacion split vicente lopez"` · `"aire acondicionado olivos"` · `"aire acondicionado florida"` |
| Instalación · San Isidro | `"aire acondicionado san isidro"` · `"instalacion split san isidro"` · `"aire acondicionado martinez"` · `"aire acondicionado acassuso"` |
| Instalación · Tigre | `"aire acondicionado tigre"` · `"instalacion split tigre"` · `"aire acondicionado don torcuato"` |
| Instalación · Nordelta | `"aire acondicionado nordelta"` · `"instalacion aire acondicionado nordelta"` · `"aire acondicionado barrio cerrado"` · `"aire acondicionado country"` |
| Instalación · Pilar | `"aire acondicionado pilar"` · `"instalacion split pilar"` · `"aire acondicionado pilar del este"` |
| Multisplit y conductos | `"instalacion multisplit"` · `"aire acondicionado por conductos"` · `"instalacion piso techo"` · `"aire acondicionado cassette"` |

**Campaña Recambio y urgencia** (menos competida y con la intención más alta de todas):

`"cambiar aire acondicionado"` · `"reemplazo aire acondicionado"` · `"aire acondicionado no enfria"` · `"aire acondicionado pierde agua"` · `[urgencia aire acondicionado]` · `"reparacion aire acondicionado urgente"` · `"tecnico aire acondicionado hoy"`

**Campaña Service y mantenimiento** (la que sostiene el invierno):

`"service aire acondicionado"` · `"mantenimiento aire acondicionado"` · `"limpieza aire acondicionado"` · `"carga de gas aire acondicionado"` · `"tecnico aire acondicionado zona norte"` · `[service aire acondicionado precio]`

**Campaña Marca**: `[clima baires]` · `"clima baires"` · `"climabaires"`.

## 18.4 Negativas — la lista que hay que cargar el día 1

Se carga como **lista compartida** aplicada a todas las campañas. Sale del histórico de Málaga, adaptada al léxico argentino:

| Grupo | Términos |
|---|---|
| **Sin intención de compra** | gratis · como hacer · diy · hazlo tu mismo · tutorial · manual · pdf · curso · aprender |
| **Trabajo** | empleo · trabajo · curso instalador · matricula · se busca · vacante · sueldo |
| **Segunda mano y alquiler** | usado · segunda mano · alquiler · alquilar · permuta · marketplace |
| **Repuestos y partes** | repuesto · placa · control remoto · turbina · capacitor · filtro · soporte |
| **Fuera de negocio** | portatil · pinguino · ventilador · calefactor · estufa · caloventor · aire de auto · automotor · heladera · freezer |
| **Fuera de zona** | cordoba · rosario · mendoza · la plata · mar del plata · quilmes · lomas de zamora · lanus · avellaneda |
| **Comparadores y competencia** | opiniones · quejas · reclamos · mercadolibre · fravega · musimundo · garbarino |

> **Rutina obligatoria de los primeros 90 días:** el informe de términos de búsqueda se revisa **los lunes**, sin excepción. Cada término irrelevante que se convierte en negativa es presupuesto que vuelve al pico de diciembre. En los primeros dos meses esta media hora semanal es la acción de mayor retorno de toda la cuenta.

## 18.5 Anuncios

Anuncios adaptables de búsqueda, uno por grupo, con la zona en el título cuando el grupo es local. Títulos (máximo 30 caracteres):

| # | Título |
|---|---|
| 1 | Aire Acondicionado en {Zona} |
| 2 | Precio Cerrado, Sin Sorpresas |
| 3 | Instalación Certificada |
| 4 | Presupuesto en el Día |
| 5 | Entramos a Countries |
| 6 | Posventa que Responde |
| 7 | Calculá Tus Frigorías Gratis |
| 8 | Venta + Instalación + Service |
| 9 | Clima Baires — Zona Norte |
| 10 | Respondemos por WhatsApp |

Descripciones (máximo 90 caracteres):

1. `Equipo, materiales e instalación en un solo precio cerrado. Lo que ves es lo que pagás.`
2. `Presupuesto el mismo día por WhatsApp. Visita técnica sin cargo en el corredor norte.`
3. `Seguros al día y cláusula de no repetición: entramos a countries y barrios cerrados.`
4. `De Málaga a Buenos Aires: instalación certificada con checklist y garantía escrita.`

**Fijar en la posición 1** el título con la zona en los grupos locales; el resto rota. Y una regla editorial que vale más que cualquier optimización: **el anuncio no promete nada que la web no confirme**. Si el anuncio dice «precio cerrado», la landing tiene que mostrar cómo se compone el precio — si no, sube el rebote, baja el nivel de calidad y sube el CPC.

**Extensiones** (obligatorias todas):

- **Enlaces de sitio**: Calculadora de frigorías · Instalaciones recientes · Zonas que cubrimos · Service y mantenimiento
- **Textos destacados**: Presupuesto en el día · Precio cerrado · Aptos countries · Garantía escrita · Sin anticipo para presupuestar
- **Fragmentos estructurados** (Servicios): Instalación · Recambio · Multisplit · Conductos · Mantenimiento
- **Llamada**: el WhatsApp comercial, en horario de atención
- **Formulario de clientes potenciales**: barrio, tipo de equipo, ambientes

Sin extensión de ubicación: la empresa es de área de servicio y no tiene local visible (sección 15.2).

## 18.6 Pujas: cómo se arranca y cuándo se cambia

| Momento | Estrategia | Por qué |
|---|---|---|
| **Días 1-30** | Maximizar clics con CPC máximo | Sin conversiones acumuladas, la puja automática no tiene con qué aprender. El tope evita que un clic de diciembre se lleve el día |
| **A partir de 15 conversiones** | Maximizar conversiones | Ya hay señal suficiente para que el algoritmo trabaje |
| **A partir de 30 conversiones** | CPA objetivo, arrancando en {{ars:_mk.cac}} | Se fija el costo por instalación y se deja que el sistema busque volumen dentro de ese techo |
| **Nunca** | ROAS objetivo | Requiere pasar el valor de cada conversión, y acá el valor real se conoce recién al firmar |

**Ajustes**: +20 % en móvil (de ahí llega el grueso del tráfico y es donde el botón de WhatsApp convierte mejor) y +15 % en el horario de 18 a 21 de días hábiles, que es cuando la gente resuelve la casa.

## 18.7 Los primeros 30 días, día por día

| Día | Qué se hace |
|---|---|
| 1 | Crear la cuenta bajo la MCC, facturación en ARS, importar conversiones de GA4 |
| 2 | Cargar la lista de negativas completa **antes** de encender nada |
| 3 | Montar Instalación y Recambio con sus grupos y anuncios; dejar Service y Marca en pausa |
| 4 | Encender con el 60 % del presupuesto del mes. El 40 % restante se libera cuando el CPL se estabilice |
| 8 | Primera revisión de términos de búsqueda. Habrá basura: es normal y es la más rentable de limpiar |
| 10 | Encender Marca y Service |
| 15 | Revisión de CPL por campaña. Lo que esté al doble del objetivo se pausa, no se «optimiza» |
| 22 | Segunda ronda de negativas. Subir presupuesto en el grupo con mejor coste por conversación |
| 30 | Balance del mes: CPL, conversaciones, presupuestos enviados y instalaciones cerradas. Decidir el reparto del mes siguiente |

> **Lo que no se hace el primer mes:** activar Performance Max. Necesita unas 30 conversiones de historial para no dispersar el presupuesto en tráfico irrelevante; encenderla antes es la forma más habitual de quemar el presupuesto de una cuenta nueva. Está prevista para el mes 3.
