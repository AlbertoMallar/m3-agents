# Base de Conocimiento de Tecnologia

## 1. Proposito y alcance

Esta base describe el soporte tecnologico interno de PI Cloud, empresa SaaS con equipos distribuidos. El equipo de Tecnologia atiende accesos, dispositivos, conectividad, software corporativo, incidentes y controles basicos de seguridad. No administra politicas de personal, reembolsos ni aprobaciones de gasto.

### 1.1 Canales de soporte

Los incidentes cotidianos se registran en el portal de soporte con prioridad normal. Las interrupciones que impiden trabajar se reportan en el canal interno `#it-incidentes` y se crean tambien en el portal. No se deben compartir contrasenas, codigos MFA ni informacion de clientes en mensajes de soporte.

### 1.2 Horario y severidad

Soporte atiende dias habiles de 9:00 a 18:00 hora de Argentina. Una caida general de VPN, correo, inicio de sesion o produccion es severidad alta. Una solicitud de software, equipo o permiso sin bloqueo inmediato es severidad normal. El equipo informa el avance por el ticket.

## 2. Cuentas, contrasenas y MFA

### 2.1 Cuenta corporativa

Cada persona recibe una cuenta corporativa durante onboarding. Esa cuenta es individual, no puede compartirse y se usa para correo, calendario, repositorios, VPN y herramientas autorizadas. Las cuentas de terceros requieren aprobacion del responsable del sistema y del manager solicitante.

### 2.2 Restablecimiento de contrasena

Si se olvida la contrasena, la persona debe usar el flujo de recuperacion del proveedor corporativo. Si no puede completar la verificacion, debe abrir un ticket desde un canal alternativo e indicar su usuario corporativo. Soporte verifica identidad antes de restablecer el acceso. Nunca solicita la contrasena actual ni codigos de un autenticador.

### 2.3 Autenticacion multifactor

MFA es obligatorio para todas las cuentas corporativas. Se permite una aplicacion autenticadora o una llave de seguridad aprobada. Al cambiar o perder el telefono, se debe registrar un ticket de recuperacion MFA; despues de verificar identidad, Soporte elimina el factor perdido y guia el alta del nuevo dispositivo.

### 2.4 Codigos y dispositivos de respaldo

Los codigos de respaldo se guardan en el gestor de contrasenas corporativo o en una ubicacion personal segura aprobada. No se almacenan en chats, notas compartidas ni capturas de pantalla. Un dispositivo MFA perdido debe reportarse el mismo dia para revocar sesiones si corresponde.

## 3. Accesos y permisos

### 3.1 Principio de minimo privilegio

Los permisos se otorgan solo para las tareas necesarias y por el menor tiempo razonable. El acceso a produccion, datos de clientes, finanzas y administracion de identidades requiere justificacion y aprobacion explicita del responsable del recurso.

### 3.2 Solicitud de acceso

Un ticket de acceso debe incluir sistema, nivel requerido, motivo de negocio, manager y fecha de vencimiento si es temporal. El manager valida la necesidad; el propietario del sistema aprueba los accesos sensibles. Soporte implementa la asignacion y deja constancia en el ticket.

### 3.3 Cambios de rol y bajas

People Operations informa los cambios de rol y salidas. Tecnologia revisa grupos, licencias, llaves y sesiones segun el proceso de offboarding. Los managers deben informar con anticipacion los cambios planificados para evitar accesos innecesarios o bloqueos de trabajo.

### 3.4 Acceso de proveedores

Un proveedor recibe una cuenta separada, temporal y limitada al sistema contratado. Debe tener sponsor interno, fecha de expiracion y acuerdo de confidencialidad vigente. No se reutilizan cuentas de empleados para terceros.

## 4. VPN y conectividad

### 4.1 Uso de VPN

La VPN corporativa es obligatoria para acceder a recursos internos, ambientes administrativos y servicios restringidos. Se debe usar el cliente aprobado por PI Cloud y mantenerlo actualizado. El acceso a aplicaciones publicas no requiere VPN salvo indicacion del sistema.

### 4.2 No puedo conectarme a la VPN

Primero se debe comprobar conexion a internet, fecha y hora correctas y estado de MFA. Luego se reinicia el cliente VPN y se intenta una unica conexion nueva. Si aparece un mensaje de error, el ticket debe incluir la hora, el codigo literal y el sistema operativo. No se deben enviar capturas que muestren tokens o direcciones de clientes.

### 4.3 Conexion lenta o inestable

Para lentitud, se recomienda desconectar sesiones VPN duplicadas, confirmar que no haya descargas personales intensivas y probar una red alternativa autorizada. Si la situacion afecta reuniones o trabajo diario, Soporte puede solicitar una prueba de velocidad y registros del cliente. No se cambia la configuracion de tuneles sin indicacion del equipo de Tecnologia.

### 4.4 Redes publicas

En redes publicas se debe usar VPN antes de abrir recursos internos. Se prohbe desactivar el firewall local o compartir archivos de trabajo en equipos publicos. Para viajes internacionales con restricciones de red, se consulta a Tecnologia antes del viaje.

## 5. Correo, calendario y colaboracion

### 5.1 Correo corporativo

El correo corporativo se usa para comunicaciones de trabajo. Los mensajes sospechosos se reportan con el boton de phishing o mediante ticket, sin reenviarlos a contactos externos. Los reenvios automaticos a cuentas personales no estan permitidos.

### 5.2 Calendario y reuniones

Las reuniones con participantes externos deben usar enlaces corporativos y configuraciones de espera cuando se comparta informacion sensible. Las grabaciones se habilitan solo si existe necesidad de negocio y los participantes son informados.

### 5.3 Chat y archivos

Los archivos internos se comparten en las plataformas corporativas autorizadas. No se usan cuentas personales de almacenamiento para documentos de PI Cloud. Los canales publicos internos no deben contener secretos, datos de clientes ni credenciales.

## 6. Software corporativo

### 6.1 Catalogo aprobado

Tecnologia mantiene un catalogo de aplicaciones aprobadas para productividad, desarrollo, seguridad y comunicacion. Antes de instalar una herramienta nueva se debe verificar si ya existe una alternativa aprobada. Las licencias se asignan por necesidad de rol.

### 6.2 Solicitud de software

El ticket debe indicar nombre del software, proveedor, uso previsto, usuarios involucrados, tipo de datos procesados y urgencia. Seguridad y Compras pueden revisar aplicaciones que procesen datos personales, datos de clientes o credenciales. No se aceptan terminos de servicio a nombre de PI Cloud sin la aprobacion correspondiente.

### 6.3 Actualizaciones

Las actualizaciones criticas de seguridad deben instalarse cuando el sistema las solicite o dentro de la ventana indicada por Tecnologia. Las actualizaciones de herramientas de desarrollo se coordinan si pueden afectar proyectos activos. No se deshabilita la gestion automatica del equipo.

### 6.4 Software no autorizado

No se instala software pirata, herramientas de acceso remoto no aprobadas ni extensiones que soliciten permisos excesivos. Si una aplicacion bloquea el trabajo, se informa en el ticket; no se evita el control mediante cuentas personales o dispositivos no administrados.

## 7. Hardware y dispositivos

### 7.1 Equipos asignados

PI Cloud entrega equipos administrados segun rol y disponibilidad. El equipo sigue siendo propiedad de la empresa y debe mantenerse actualizado, cifrado y protegido con bloqueo de pantalla. No se permite prestar equipos corporativos a familiares o terceros.

### 7.2 Problemas de laptop

Ante fallas de bateria, pantalla, teclado, camara o rendimiento, se abre un ticket con el numero de activo y una descripcion reproducible. Antes de reiniciar o actualizar, se debe guardar el trabajo y sincronizar archivos corporativos. Soporte define si requiere diagnostico remoto, reparacion o reemplazo.

### 7.3 Perifericos y ergonomia

Los perifericos estandar se solicitan por el portal de Tecnologia. Las necesidades ergonomicas se coordinan con People Operations y el manager; Tecnologia instala o configura el equipamiento aprobado. No se compran perifericos por cuenta propia esperando reembolso sin el flujo financiero correspondiente.

### 7.4 Equipo perdido o robado

La perdida o robo de un dispositivo corporativo se reporta de inmediato al canal de incidentes y al manager. Tecnologia puede bloquear el equipo, cerrar sesiones y borrar datos administrados. La persona debe presentar la denuncia cuando sea requerida por la politica local.

## 8. Troubleshooting estandar

### 8.1 Antes de abrir un ticket

Se recomienda verificar si existe una incidencia conocida, reiniciar solo la aplicacion afectada, cerrar sesiones duplicadas y anotar mensajes de error. No se eliminan perfiles, registros ni configuraciones avanzadas para intentar resolver un problema.

### 8.2 Informacion util para soporte

Un buen ticket contiene impacto, hora de inicio, pasos para reproducir, mensaje de error, sistema operativo, aplicacion y si el problema afecta a mas personas. Las capturas deben ocultar datos de clientes, tokens, secretos y conversaciones privadas.

### 8.3 Problemas de navegador

Si una aplicacion web falla, se prueba una ventana privada y se confirma que el navegador este actualizado. Se pueden deshabilitar extensiones no esenciales una por una. Borrar datos del navegador debe hacerse solo si no se perderan sesiones o informacion necesaria.

### 8.4 Aplicacion bloqueada

Si una aplicacion se congela, se espera un momento, se registra el error y luego se cierra mediante el sistema operativo si no responde. Los reportes de fallas recurrentes deben incluir frecuencia y archivos o acciones involucradas, sin adjuntar datos sensibles.

## 9. Incidentes y operaciones

### 9.1 Que es un incidente

Un incidente es una degradacion no planificada de un servicio, una brecha de seguridad sospechada o una perdida de acceso que afecta operaciones. Los cambios planificados y solicitudes de mejora se registran como tickets normales, salvo que causen interrupcion.

### 9.2 Reporte de incidente

El primer reporte debe indicar servicio afectado, impacto, hora de deteccion y contacto disponible. El responsable de guardia coordina la investigacion y publica actualizaciones en el canal definido. Las personas usuarias no deben realizar cambios en produccion para resolver por su cuenta.

### 9.3 Comunicacion durante incidentes

Solo el responsable de incidente o la persona designada comunica estado externo. Los canales internos pueden incluir detalles tecnicos necesarios, pero no secretos. Al finalizar, se documentan causa, impacto, acciones correctivas y responsables de seguimiento.

### 9.4 Cambios de emergencia

Un cambio de emergencia requiere registro posterior, revision tecnica y aprobacion del responsable disponible. Se limita a restaurar el servicio o mitigar el riesgo. No se aprovecha una emergencia para desplegar mejoras no relacionadas.

## 10. Seguridad tecnica basica

### 10.1 Phishing e ingenieria social

Se desconfia de solicitudes urgentes de credenciales, pagos, codigos MFA o cambios de cuenta bancaria. Un mensaje que imita a un ejecutivo, proveedor o soporte debe verificarse por un canal independiente. Los correos sospechosos se reportan, no se responden.

### 10.2 Secretos y claves

Las claves API, tokens y certificados se almacenan solo en el gestor de secretos aprobado. Nunca se incluyen en repositorios, tickets publicos, chat o documentos compartidos. Un secreto expuesto se rota de inmediato y se reporta como incidente de seguridad.

### 10.3 Datos de clientes

El acceso a datos de clientes se limita a la necesidad operativa. No se descargan bases completas para pruebas locales. Los ambientes de desarrollo deben usar datos anonimizados o sinteticos cuando sea posible.

### 10.4 Bloqueo y cifrado

Todos los equipos corporativos usan cifrado de disco y bloqueo automatico de pantalla. Se debe bloquear la sesion al alejarse del equipo. No se deshabilitan agentes de seguridad, antivirus ni administracion remota.

## 11. Desarrollo e infraestructura

### 11.1 Repositorios y control de versiones

El codigo se almacena en los repositorios corporativos. Las ramas protegidas requieren revision y controles automatizados definidos por el equipo. No se suben secretos ni datos reales de clientes al repositorio.

### 11.2 Acceso a produccion

El acceso a produccion es limitado, auditado y usado solo para tareas autorizadas. Las operaciones de alto impacto requieren el procedimiento del equipo responsable y, cuando aplique, una segunda persona. Los accesos temporales expiran al finalizar la tarea.

### 11.3 Ambientes y despliegues

Los cambios pasan por los ambientes definidos antes de produccion, salvo emergencia declarada. Un despliegue debe incluir plan de reversa y monitoreo posterior. Los errores se reportan con el identificador del despliegue y el servicio afectado.

### 11.4 Integraciones

Las nuevas integraciones requieren revision de propietario, permisos, datos compartidos y plan de revocacion. Los webhooks y credenciales se registran en el gestor de secretos. No se conectan servicios personales a sistemas corporativos.

## 12. Preguntas frecuentes

### 12.1 Tengo una nueva computadora

Se debe seguir la guia de configuracion administrada, activar MFA y verificar VPN, correo y herramientas principales. Si falta acceso a un sistema, se abre un ticket de permisos; no se usa la cuenta de otra persona.

### 12.2 No recibo codigos MFA

Se confirma la hora del telefono y la aplicacion autenticadora. Si el dispositivo fue cambiado o perdido, se abre un ticket de recuperacion MFA. Soporte valida identidad antes de restablecer factores.

### 12.3 Un enlace parece sospechoso

No se abre ni se ingresa informacion. Se reporta por el boton de phishing o se reenvia como adjunto al canal de Seguridad indicado. Si se ingresaron credenciales, se cambia la contrasena y se avisa de inmediato.

### 12.4 La VPN funciona pero un sistema interno no

Se verifica el mensaje de error, se prueba una sesion nueva y se revisa si el servicio tiene un incidente activo. Si persiste, el ticket debe incluir sistema, hora, usuario afectado y evidencia sin secretos.

## 13. Actualizacion del documento

Tecnologia revisa esta base trimestralmente y despues de incidentes relevantes. Ante conflicto con un procedimiento aprobado mas reciente, prevalece la comunicacion oficial del propietario del sistema.

## 14. Trabajo remoto y continuidad

### 14.1 Puesto de trabajo remoto

La persona que trabaja remotamente debe contar con una red razonablemente estable, equipo corporativo y espacio que evite la exposicion de informacion en pantallas o conversaciones. Tecnologia brinda soporte sobre el equipo y las herramientas, pero no modifica routers personales ni instala cableado domiciliario.

### 14.2 Interrupcion de conectividad local

Si la red domestica falla, se debe informar al manager y usar una alternativa segura cuando sea posible, como una conexion movil aprobada. Si la interrupcion es prolongada, el ticket debe diferenciar si afecta internet general, VPN o una aplicacion concreta para que Soporte pueda orientar correctamente.

### 14.3 Continuidad ante una caida amplia

Cuando un servicio corporativo presenta una caida general, las personas deben consultar el canal oficial de incidentes y evitar abrir tickets duplicados. Los equipos pueden usar procedimientos manuales aprobados para continuar tareas criticas, pero no deben mover datos a herramientas personales para sortear la interrupcion.

## 15. Ciclo de solicitudes de Tecnologia

### 15.1 Estados de un ticket

Un ticket puede estar nuevo, en analisis, esperando informacion, en curso, resuelto o cerrado. Si Soporte solicita datos adicionales, la persona debe responder en el mismo ticket para conservar el historial. Los tickets resueltos pueden reabrirse si el mismo problema reaparece dentro de los cinco dias habiles.

### 15.2 Prioridad y expectativa

La prioridad refleja impacto y urgencia, no jerarquia de quien solicita. Un bloqueo individual recibe atencion antes que una mejora menor, y una incidencia que afecta a varias personas se coordina como incidente. Soporte comunica tiempos estimados cuando la investigacion lo permite, sin prometer una solucion antes de confirmar la causa.

### 15.3 Cierre de solicitud

Antes de cerrar un ticket, Soporte registra la accion aplicada y, cuando corresponde, solicita confirmacion de la persona usuaria. Si la solucion requiere un cambio de conducta o configuracion, se incluye una guia breve para evitar recurrencias. Los tickets de seguridad pueden cerrarse con informacion limitada para proteger detalles sensibles.
