# Product Backlog — MVP de Origin Link

> Generado por `scripts/backlog.py md`. Para cambiar el backlog, editar ese archivo y regenerar.

Fuentes: matriz de trazabilidad (Project Charter 4.1), matriz de necesidades por actor (Anexo 5) y EDT.

## Resumen

- **8 épicas**, **24 historias de usuario** y **1 tarea técnica** (TT: habilitadores sin usuario final).
- **MVP:** 25 ítems, 87 story points. Todas las historias se construyeron en los dos sprints; Should y Could indican prioridad, no exclusión del alcance.
- **Sprint 1** (05/10–20/10/2026: identidad, proveedores, lotes, compras y recepciones, modelo TCN y datos sintéticos): 14 ítems, 47 pts comprometidos, 39 completados. HU-19 (8 pts) pasó al Sprint 2 por el retraso del hito H06 (+2 días).
- **Sprint 2** (21/10–03/11/2026: inventario, pronóstico, recomendaciones, alertas y comparación de proveedores): 11 ítems nuevos (40 pts) más 8 pts del Sprint 1: 48 pts completados.

## Flujo del MVP (User Story Mapping simplificado)

| Actividad del usuario | Sprint 1 | Sprint 2 |
|---|---|---|
| EP-01 Identidad y acceso | HU-01, HU-02, HU-03, HU-04 | — |
| EP-02 Proveedores y relaciones privadas | HU-05, HU-06, HU-07 | — |
| EP-03 Gestión colaborativa de lotes | HU-08, HU-11, HU-12 | HU-09, HU-10 |
| EP-04 Compras y recepciones | HU-13, HU-14 | HU-15 |
| EP-05 Inventario y existencias | — | HU-16, HU-17, HU-18 |
| EP-06 Pronóstico de demanda con TCN | HU-19 (→ S2), TT-01 | HU-20 |
| EP-07 Recomendaciones de abastecimiento y alertas | — | HU-21, HU-22 |
| EP-08 Comparación de lotes y desempeño de proveedores | — | HU-23, HU-24 |

## Product Backlog priorizado

Ordenado por valor para el negocio dentro de cada grupo MoSCoW: primero el pronóstico y las recomendaciones (OE3), luego el flujo colaborativo de lotes, compras e inventario (OE2) y al final la identidad y el acceso, que son habilitadores. El ID solo identifica la historia.

| N.° | ID | Historia | Épica | Prioridad | Pts | Sprint | Área | Trazabilidad |
|---|---|---|---|---|---|---|---|---|
| 1 | HU-19 | Entrenar y evaluar el modelo TCN | EP-06 | Must | 8 | Sprint 1 → terminada en Sprint 2 | ml | Req. 3.1 · OE3 · EDT 1.5.1.2, 1.5.2.1, 1.5.2.3 |
| 2 | HU-20 | Ver el pronóstico de consumo de las próximas semanas | EP-06 | Must | 5 | Sprint 2 | backend, frontend, ml | Req. 3.0 · OE3 · EDT 1.5.3, 1.5.5 |
| 3 | HU-21 | Recibir una recomendación de cuánto y cuándo comprar | EP-07 | Must | 8 | Sprint 2 | backend, frontend | Req. 3.2 · OE3 · EDT 1.5.4.1, 1.5.4.2 |
| 4 | HU-22 | Recibir alertas de stock bajo y próxima compra | EP-07 | Must | 3 | Sprint 2 | backend, frontend | Req. 3.2 · OE3 · EDT 1.5.4.3 |
| 5 | HU-08 | Publicar un lote de café verde | EP-03 | Must | 5 | Sprint 1 | backend, frontend | Req. 1.2 · OE2 · EDT 1.4.4.1, 1.4.4.2 |
| 6 | HU-09 | Consultar los lotes de mis proveedores | EP-03 | Must | 3 | Sprint 2 | backend, frontend | Req. 1.2 · OE2 · EDT 1.4.4.5 |
| 7 | HU-10 | Actualizar disponibilidad y condiciones de abastecimiento | EP-03 | Must | 3 | Sprint 2 | backend, frontend | Req. 1.2 · OE2 · EDT 1.4.4.4 |
| 8 | HU-13 | Registrar una compra | EP-04 | Must | 3 | Sprint 1 | backend, frontend | Req. 2.1 · OE2 · EDT 1.4.5.1 |
| 9 | HU-14 | Registrar la recepción de una compra | EP-04 | Must | 3 | Sprint 1 | backend, frontend | Req. 2.1 · OE2 · EDT 1.4.5.2 |
| 10 | HU-16 | Registrar consumos, mermas y ajustes | EP-05 | Must | 3 | Sprint 2 | backend, frontend | Req. 2.1.1 · OE2 · EDT 1.4.6.1 |
| 11 | HU-17 | Ver mis existencias actuales | EP-05 | Must | 2 | Sprint 2 | backend, frontend | Req. 2.1.1 · OE2 · EDT 1.4.6.2 |
| 12 | HU-18 | Importar mi historial de consumo | EP-05 | Must | 3 | Sprint 2 | backend, frontend | Req. 2.1.1 y 3.1 · OE2, OE3 · EDT 1.4.6.1, 1.5.1.1 · Anexo 5 (entrevista 4) |
| 13 | TT-01 | Cargar los datos sintéticos de demostración (seed) | EP-06 | Must | 5 | Sprint 1 | backend, ml | Plan de contingencia H06a · OE3 · EDT 1.5.1.2 |
| 14 | HU-05 | Registrar un proveedor | EP-02 | Must | 2 | Sprint 1 | backend, frontend | Req. 1.1 · OE2 · EDT 1.4.3.1 |
| 15 | HU-06 | Invitar a un proveedor a vincularse | EP-02 | Must | 3 | Sprint 1 | backend, frontend | Req. 1.1 · OE2 · EDT 1.4.3.2 |
| 16 | HU-07 | Ver mis vínculos | EP-02 | Must | 2 | Sprint 1 | backend, frontend | Req. 1.1 · OE2 · EDT 1.4.3.2 |
| 17 | HU-03 | Crear cuenta de cooperativa desde una invitación | EP-01 | Must | 3 | Sprint 1 | backend, frontend | Req. 5.0 y 1.1 · OE2 · EDT 1.4.2.1, 1.4.3.2 |
| 18 | HU-04 | Restringir el acceso según el rol y el vínculo | EP-01 | Must | 2 | Sprint 1 | backend | Req. 5.0 · OE2 · EDT 1.4.2.2 |
| 19 | HU-01 | Registrar cuenta de tostador | EP-01 | Must | 3 | Sprint 1 | backend, frontend | Req. 5.0 · OE2 · EDT 1.4.2.1 |
| 20 | HU-02 | Iniciar y cerrar sesión | EP-01 | Must | 3 | Sprint 1 | backend, frontend | Req. 5.0 · OE2 · EDT 1.4.2.1 |
| 21 | HU-23 | Comparar lotes de mis proveedores vinculados | EP-08 | Should | 5 | Sprint 2 | frontend, backend | Req. 4.0 · OE2 · EDT 1.4.4.6 |
| 22 | HU-11 | Registrar un lote de un proveedor sin cuenta | EP-03 | Should | 2 | Sprint 1 | backend, frontend | Req. 1.2 · OE2 · EDT 1.4.4.1 |
| 23 | HU-15 | Consultar el historial de compras por proveedor | EP-04 | Should | 2 | Sprint 2 | backend, frontend | Req. 2.1 · OE2 · EDT 1.4.5.3 |
| 24 | HU-12 | Adjuntar muestras, fichas técnicas y documentos a un lote | EP-03 | Could | 3 | Sprint 1 | backend, frontend | Req. 1.2.1 · OE2 · EDT 1.4.4.3 |
| 25 | HU-24 | Ver el cumplimiento histórico de un proveedor | EP-08 | Could | 3 | Sprint 2 | backend, frontend | Req. 4.0 · OE3 · EDT 1.4.5.3 |

## Definition of Ready (DoR)

Una historia entra a un sprint solo si:

1. Tiene el formato Como / Quiero / Para y criterios de aceptación verificables en Gherkin.
2. Está estimada en story points y priorizada por el Product Owner.
3. Tiene definido el contrato de API y/o el diseño de la pantalla.
4. No tiene dependencias bloqueantes con historias no terminadas.
5. Tiene trazabilidad a un requisito, un objetivo específico y un paquete de la EDT.

## Definition of Done (DoD)

Una historia está terminada solo si:

1. Cumple todos sus criterios de aceptación.
2. Tiene pruebas escritas antes del código (TDD) y el CI está en verde.
3. Fue revisada y probada por otro integrante (prueba cruzada).
4. Está unida a `develop` mediante un PR con `Closes #<issue>`.
5. Se desplegó en el ambiente de validación sin errores.

## Detalle de épicas e historias

### EP-01: Identidad y acceso

#### Descripción
Registro, inicio de sesión y control de acceso por rol para tostadores y empresas productoras o cooperativas. Una cooperativa solo puede entrar a la plataforma por invitación de un tostador.

#### Objetivo específico y paquete EDT
OE2 · Requisito 5.0 · EDT 1.4.2

#### Valor para el usuario
Garantiza la privacidad comercial: cada tostador ve solo su información y la de sus proveedores vinculados.

#### Historias de usuario
- HU-01: Registrar cuenta de tostador (Must, 3 pts, Sprint 1)
- HU-02: Iniciar y cerrar sesión (Must, 3 pts, Sprint 1)
- HU-03: Crear cuenta de cooperativa desde una invitación (Must, 3 pts, Sprint 1)
- HU-04: Restringir el acceso según el rol y el vínculo (Must, 2 pts, Sprint 1)


#### HU-01: Registrar cuenta de tostador

##### Épica
EP-01: Identidad y acceso

##### Historia
**Como** tostador
**quiero** registrarme con el nombre de mi empresa, mi correo y una contraseña
**para** gestionar mi abastecimiento de café verde en un solo lugar

##### Criterios de aceptación (Gherkin)
**Escenario 1: Registro exitoso**
- **Dado** que ingreso nombre de empresa, correo válido y contraseña de al menos 8 caracteres
- **Cuando** envío el formulario
- **Entonces** se crea mi cuenta con rol tostador y entro a mi panel

**Escenario 2: Correo duplicado**
- **Dado** que ya existe una cuenta con mi correo
- **Cuando** envío el formulario
- **Entonces** veo el mensaje "Ya existe una cuenta con este correo" y no se crea otra

##### Trazabilidad
Req. 5.0 · OE2 · EDT 1.4.2.1

##### Prioridad (MoSCoW)
Must

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-02: Iniciar y cerrar sesión

##### Épica
EP-01: Identidad y acceso

##### Historia
**Como** usuario de Origin Link
**quiero** iniciar sesión con mi correo y contraseña y cerrarla cuando termine
**para** acceder de forma segura a mi información

##### Criterios de aceptación (Gherkin)
**Escenario 1: Credenciales correctas**
- **Dado** que tengo una cuenta registrada
- **Cuando** ingreso mi correo y contraseña correctos
- **Entonces** entro a la plataforma según mi rol (tostador o cooperativa)

**Escenario 2: Credenciales incorrectas**
- **Dado** que ingreso una contraseña equivocada
- **Cuando** intento iniciar sesión
- **Entonces** veo "Correo o contraseña incorrectos" sin indicar cuál de los dos falló

**Escenario 3: Cerrar sesión**
- **Dado** que tengo la sesión iniciada
- **Cuando** hago clic en "Cerrar sesión"
- **Entonces** vuelvo a la pantalla de inicio de sesión y no puedo acceder sin ingresar de nuevo

##### Trazabilidad
Req. 5.0 · OE2 · EDT 1.4.2.1

##### Prioridad (MoSCoW)
Must

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-03: Crear cuenta de cooperativa desde una invitación

##### Épica
EP-01: Identidad y acceso

##### Historia
**Como** empresa productora o cooperativa
**quiero** crear mi cuenta usando la invitación que me envió un tostador
**para** compartir mis lotes con ese tostador sin exponerlos públicamente

##### Criterios de aceptación (Gherkin)
**Escenario 1: Invitación válida**
- **Dado** que recibí un enlace de invitación vigente
- **Cuando** lo abro y completo mis datos
- **Entonces** se crea mi cuenta con rol cooperativa y quedo vinculado con el tostador que me invitó

**Escenario 2: Sin invitación**
- **Dado** que no tengo invitación
- **Cuando** intento registrarme como cooperativa
- **Entonces** el sistema no me permite crear la cuenta

**Escenario 3: Invitación vencida o usada**
- **Dado** que el enlace ya fue usado o venció
- **Cuando** lo abro
- **Entonces** veo "Invitación no válida" y la indicación de pedir una nueva al tostador

##### Trazabilidad
Req. 5.0 y 1.1 · OE2 · EDT 1.4.2.1, 1.4.3.2

##### Prioridad (MoSCoW)
Must

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-04: Restringir el acceso según el rol y el vínculo

##### Épica
EP-01: Identidad y acceso

##### Historia
**Como** tostador
**quiero** que solo mis proveedores vinculados puedan ver mi información y yo solo la de ellos
**para** mantener la privacidad comercial de mis compras

##### Criterios de aceptación (Gherkin)
**Escenario 1: Acceso a datos propios**
- **Dado** que soy un tostador con sesión iniciada
- **Cuando** consulto mis compras e inventario
- **Entonces** solo veo registros de mi empresa

**Escenario 2: Acceso no autorizado**
- **Dado** que una cooperativa no está vinculada conmigo
- **Cuando** intenta consultar mis datos o lotes compartidos conmigo
- **Entonces** la API responde 403 y no muestra información

##### Trazabilidad
Req. 5.0 · OE2 · EDT 1.4.2.2

##### Prioridad (MoSCoW)
Must

##### Story points
2

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


### EP-02: Proveedores y relaciones privadas

#### Descripción
El tostador registra a sus proveedores de café verde y los invita a vincularse de forma privada.

#### Objetivo específico y paquete EDT
OE2 · Requisito 1.1 · EDT 1.4.3

#### Valor para el usuario
Reemplaza la coordinación informal por WhatsApp y hojas de cálculo (entrevista 1) por un canal privado y ordenado.

#### Historias de usuario
- HU-05: Registrar un proveedor (Must, 2 pts, Sprint 1)
- HU-06: Invitar a un proveedor a vincularse (Must, 3 pts, Sprint 1)
- HU-07: Ver mis vínculos (Must, 2 pts, Sprint 1)


#### HU-05: Registrar un proveedor

##### Épica
EP-02: Proveedores y relaciones privadas

##### Historia
**Como** tostador
**quiero** registrar a mis proveedores con su nombre, región de origen y datos de contacto
**para** tener centralizada la información de quién me abastece

##### Criterios de aceptación (Gherkin)
**Escenario 1: Registro de proveedor**
- **Dado** que estoy en la sección Proveedores
- **Cuando** ingreso nombre, región y contacto y guardo
- **Entonces** el proveedor aparece en mi lista con estado "Sin vincular"

**Escenario 2: Datos obligatorios**
- **Dado** que dejo vacío el nombre del proveedor
- **Cuando** intento guardar
- **Entonces** veo que el nombre es obligatorio y no se guarda

##### Trazabilidad
Req. 1.1 · OE2 · EDT 1.4.3.1

##### Prioridad (MoSCoW)
Must

##### Story points
2

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-06: Invitar a un proveedor a vincularse

##### Épica
EP-02: Proveedores y relaciones privadas

##### Historia
**Como** tostador
**quiero** generar una invitación para un proveedor registrado
**para** que pueda publicarme sus lotes directamente en la plataforma

##### Criterios de aceptación (Gherkin)
**Escenario 1: Generar invitación**
- **Dado** que tengo un proveedor "Sin vincular"
- **Cuando** hago clic en "Invitar"
- **Entonces** se genera un enlace único con vigencia de 7 días que puedo copiar y enviar

**Escenario 2: Proveedor ya vinculado**
- **Dado** que el proveedor ya está vinculado
- **Cuando** veo su ficha
- **Entonces** no se muestra la opción "Invitar"

##### Trazabilidad
Req. 1.1 · OE2 · EDT 1.4.3.2

##### Prioridad (MoSCoW)
Must

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-07: Ver mis vínculos

##### Épica
EP-02: Proveedores y relaciones privadas

##### Historia
**Como** usuario de Origin Link
**quiero** ver con quiénes estoy vinculado y el estado de cada invitación
**para** saber con quién comparto información

##### Criterios de aceptación (Gherkin)
**Escenario 1: Lista del tostador**
- **Dado** que invité a varios proveedores
- **Cuando** abro Proveedores
- **Entonces** veo cada uno con su estado: Sin vincular, Invitado o Vinculado

**Escenario 2: Lista de la cooperativa**
- **Dado** que soy una cooperativa vinculada a dos tostadores
- **Cuando** abro mi panel
- **Entonces** veo los dos tostadores con los que comparto lotes

##### Trazabilidad
Req. 1.1 · OE2 · EDT 1.4.3.2

##### Prioridad (MoSCoW)
Must

##### Story points
2

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


### EP-03: Gestión colaborativa de lotes

#### Descripción
La cooperativa publica sus lotes de café verde, su disponibilidad y condiciones de abastecimiento para los tostadores vinculados.

#### Objetivo específico y paquete EDT
OE2 · Requisitos 1.2 y 1.2.1 · EDT 1.4.4

#### Valor para el usuario
El tostador consulta información técnica y disponibilidad actualizada sin pedirla por chat (entrevistas 1, 4 y 5).

#### Historias de usuario
- HU-08: Publicar un lote de café verde (Must, 5 pts, Sprint 1)
- HU-09: Consultar los lotes de mis proveedores (Must, 3 pts, Sprint 2)
- HU-10: Actualizar disponibilidad y condiciones de abastecimiento (Must, 3 pts, Sprint 2)
- HU-11: Registrar un lote de un proveedor sin cuenta (Should, 2 pts, Sprint 1)
- HU-12: Adjuntar muestras, fichas técnicas y documentos a un lote (Could, 3 pts, Sprint 1)


#### HU-08: Publicar un lote de café verde

##### Épica
EP-03: Gestión colaborativa de lotes

##### Historia
**Como** empresa productora o cooperativa
**quiero** publicar un lote con su procedencia, variedad, proceso, cosecha, altitud, cantidad y precio
**para** que mis tostadores vinculados conozcan lo que tengo disponible

##### Criterios de aceptación (Gherkin)
**Escenario 1: Publicación exitosa**
- **Dado** que estoy vinculado con al menos un tostador
- **Cuando** registro un lote con todos sus atributos y lo publico
- **Entonces** el lote queda visible solo para mis tostadores vinculados

**Escenario 2: Validación de datos**
- **Dado** que ingreso una altitud o cantidad negativa
- **Cuando** intento publicar
- **Entonces** veo el error en el campo y el lote no se publica

##### Trazabilidad
Req. 1.2 · OE2 · EDT 1.4.4.1, 1.4.4.2

##### Prioridad (MoSCoW)
Must

##### Story points
5

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-09: Consultar los lotes de mis proveedores

##### Épica
EP-03: Gestión colaborativa de lotes

##### Historia
**Como** tostador
**quiero** ver los lotes publicados por mis proveedores vinculados con sus características
**para** decidir qué comprar con información completa

##### Criterios de aceptación (Gherkin)
**Escenario 1: Lista de lotes**
- **Dado** que mis proveedores publicaron lotes
- **Cuando** abro la sección Lotes
- **Entonces** veo cada lote con proveedor, origen, altitud, proceso, cantidad disponible y precio

**Escenario 2: Filtro**
- **Dado** que hay lotes de varios proveedores
- **Cuando** filtro por proveedor o proceso
- **Entonces** solo veo los lotes que cumplen el filtro

##### Trazabilidad
Req. 1.2 · OE2 · EDT 1.4.4.5

##### Prioridad (MoSCoW)
Must

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-10: Actualizar disponibilidad y condiciones de abastecimiento

##### Épica
EP-03: Gestión colaborativa de lotes

##### Historia
**Como** empresa productora o cooperativa
**quiero** actualizar la cantidad disponible, cantidad mínima de compra, precio y plazo de entrega de mis lotes
**para** que mis tostadores planifiquen con datos vigentes

##### Criterios de aceptación (Gherkin)
**Escenario 1: Actualización**
- **Dado** que tengo un lote publicado
- **Cuando** cambio su cantidad disponible o su plazo de entrega
- **Entonces** el tostador ve el dato nuevo y la fecha de la última actualización

**Escenario 2: Lote agotado**
- **Dado** que la cantidad disponible llega a 0
- **Cuando** guardo el cambio
- **Entonces** el lote se muestra como "Agotado"

##### Trazabilidad
Req. 1.2 · OE2 · EDT 1.4.4.4

##### Prioridad (MoSCoW)
Must

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-11: Registrar un lote de un proveedor sin cuenta

##### Épica
EP-03: Gestión colaborativa de lotes

##### Historia
**Como** tostador
**quiero** registrar yo mismo un lote de un proveedor que aún no usa la plataforma
**para** llevar el control de todo mi café verde aunque no todos mis proveedores estén vinculados

##### Criterios de aceptación (Gherkin)
**Escenario 1: Lote manual**
- **Dado** que tengo un proveedor "Sin vincular"
- **Cuando** registro un lote a su nombre
- **Entonces** el lote aparece en mi lista marcado como "Registrado por el tostador"

##### Trazabilidad
Req. 1.2 · OE2 · EDT 1.4.4.1

##### Prioridad (MoSCoW)
Should

##### Story points
2

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-12: Adjuntar muestras, fichas técnicas y documentos a un lote

##### Épica
EP-03: Gestión colaborativa de lotes

##### Historia
**Como** empresa productora o cooperativa
**quiero** adjuntar la ficha técnica y los resultados de evaluación de un lote
**para** que el tostador valide la calidad declarada

##### Criterios de aceptación (Gherkin)
**Escenario 1: Adjuntar documento**
- **Dado** que tengo un lote publicado
- **Cuando** adjunto un PDF de ficha técnica
- **Entonces** el tostador vinculado puede descargarlo desde el detalle del lote

##### Trazabilidad
Req. 1.2.1 · OE2 · EDT 1.4.4.3

##### Prioridad (MoSCoW)
Could

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


### EP-04: Compras y recepciones

#### Descripción
El tostador registra sus compras y la recepción de cada lote, incluidas las diferencias entre lo acordado y lo recibido.

#### Objetivo específico y paquete EDT
OE2 · Requisito 2.1 · EDT 1.4.5

#### Valor para el usuario
Atiende las mermas y los incumplimientos logísticos reportados en las entrevistas 1 y 2.

#### Historias de usuario
- HU-13: Registrar una compra (Must, 3 pts, Sprint 1)
- HU-14: Registrar la recepción de una compra (Must, 3 pts, Sprint 1)
- HU-15: Consultar el historial de compras por proveedor (Should, 2 pts, Sprint 2)


#### HU-13: Registrar una compra

##### Épica
EP-04: Compras y recepciones

##### Historia
**Como** tostador
**quiero** registrar una compra con el lote, la cantidad, el precio y la fecha de entrega acordada
**para** llevar el historial de mis compras por proveedor

##### Criterios de aceptación (Gherkin)
**Escenario 1: Compra de un lote publicado**
- **Dado** que un lote tiene 200 kg disponibles
- **Cuando** registro una compra de 60 kg
- **Entonces** la compra queda "Pendiente de recepción" con la fecha de entrega acordada

**Escenario 2: Cantidad mayor a la disponible**
- **Dado** que un lote tiene 50 kg disponibles
- **Cuando** intento registrar 80 kg
- **Entonces** veo una advertencia de que supera lo disponible

##### Trazabilidad
Req. 2.1 · OE2 · EDT 1.4.5.1

##### Prioridad (MoSCoW)
Must

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-14: Registrar la recepción de una compra

##### Épica
EP-04: Compras y recepciones

##### Historia
**Como** tostador
**quiero** registrar los kilos efectivamente recibidos y las observaciones
**para** detectar diferencias con lo acordado y actualizar mi inventario

##### Criterios de aceptación (Gherkin)
**Escenario 1: Recepción completa**
- **Dado** que tengo una compra pendiente de 60 kg
- **Cuando** registro la recepción de 60 kg
- **Entonces** la compra pasa a "Recibida" y se crea una entrada de inventario de 60 kg

**Escenario 2: Recepción con diferencia**
- **Dado** que tengo una compra pendiente de 60 kg
- **Cuando** registro 55 kg recibidos
- **Entonces** se registra una diferencia de -5 kg visible en la compra y la entrada de inventario es de 55 kg

##### Trazabilidad
Req. 2.1 · OE2 · EDT 1.4.5.2

##### Prioridad (MoSCoW)
Must

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-15: Consultar el historial de compras por proveedor

##### Épica
EP-04: Compras y recepciones

##### Historia
**Como** tostador
**quiero** ver el historial de compras y recepciones de cada proveedor
**para** negociar con información y no de memoria

##### Criterios de aceptación (Gherkin)
**Escenario 1: Historial**
- **Dado** que hice varias compras a un proveedor
- **Cuando** abro su ficha
- **Entonces** veo sus compras con fechas, kilos acordados, kilos recibidos y diferencias

##### Trazabilidad
Req. 2.1 · OE2 · EDT 1.4.5.3

##### Prioridad (MoSCoW)
Should

##### Story points
2

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


### EP-05: Inventario y existencias

#### Descripción
Registro de movimientos de café verde y cálculo de existencias a partir de ellos.

#### Objetivo específico y paquete EDT
OE2 · Requisito 2.1.1 · EDT 1.4.6

#### Valor para el usuario
El tostador conoce su stock real y evita quiebres; además genera el historial de consumo que alimenta al modelo TCN.

#### Historias de usuario
- HU-16: Registrar consumos, mermas y ajustes (Must, 3 pts, Sprint 2)
- HU-17: Ver mis existencias actuales (Must, 2 pts, Sprint 2)
- HU-18: Importar mi historial de consumo (Must, 3 pts, Sprint 2)


#### HU-16: Registrar consumos, mermas y ajustes

##### Épica
EP-05: Inventario y existencias

##### Historia
**Como** tostador
**quiero** registrar los kilos de café verde que consumo en el tostado, las mermas y los ajustes de inventario
**para** mantener mis existencias al día

##### Criterios de aceptación (Gherkin)
**Escenario 1: Consumo**
- **Dado** que tengo 40 kg de un lote
- **Cuando** registro un consumo de 8 kg
- **Entonces** las existencias de ese lote quedan en 32 kg

**Escenario 2: Consumo mayor a las existencias**
- **Dado** que tengo 5 kg de un lote
- **Cuando** intento registrar un consumo de 8 kg
- **Entonces** veo un error y el movimiento no se registra

**Escenario 3: Ajuste con motivo**
- **Dado** que hago un conteo físico
- **Cuando** registro un ajuste
- **Entonces** el sistema me exige indicar el motivo

##### Trazabilidad
Req. 2.1.1 · OE2 · EDT 1.4.6.1

##### Prioridad (MoSCoW)
Must

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-17: Ver mis existencias actuales

##### Épica
EP-05: Inventario y existencias

##### Historia
**Como** tostador
**quiero** ver cuántos kilos tengo de cada lote y en total
**para** saber con qué cuento antes de planificar compras

##### Criterios de aceptación (Gherkin)
**Escenario 1: Existencias calculadas**
- **Dado** que registré entradas, consumos, mermas y ajustes
- **Cuando** abro Inventario
- **Entonces** veo las existencias por lote calculadas como entradas - consumos - mermas ± ajustes

**Escenario 2: Total y lotes agotados**
- **Dado** que tengo café de varios lotes y uno ya se consumió por completo
- **Cuando** abro Inventario
- **Entonces** veo el total en kg como la suma de todos mis lotes y el lote consumido no aparece en la lista

##### Trazabilidad
Req. 2.1.1 · OE2 · EDT 1.4.6.2

##### Prioridad (MoSCoW)
Must

##### Story points
2

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-18: Importar mi historial de consumo

##### Épica
EP-05: Inventario y existencias

##### Historia
**Como** tostador
**quiero** cargar mi historial de consumo desde un archivo CSV o Excel
**para** no duplicar el trabajo que ya hice en mis hojas de cálculo y obtener pronósticos desde el primer día

##### Criterios de aceptación (Gherkin)
**Escenario 1: Importación válida**
- **Dado** que tengo un archivo con columnas fecha y kg_consumidos
- **Cuando** lo cargo
- **Entonces** veo cuántas semanas se importaron y el historial queda disponible para el pronóstico

**Escenario 2: Archivo con errores**
- **Dado** que el archivo tiene fechas inválidas o kilos negativos
- **Cuando** lo cargo
- **Entonces** veo las filas con error y no se importa ninguna hasta corregirlas

##### Trazabilidad
Req. 2.1.1 y 3.1 · OE2, OE3 · EDT 1.4.6.1, 1.5.1.1 · Anexo 5 (entrevista 4)

##### Prioridad (MoSCoW)
Must

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


### EP-06: Pronóstico de demanda con TCN

#### Descripción
Entrenamiento, evaluación y servicio del modelo TCN que pronostica el consumo semanal del tostador, con el promedio móvil de 4 semanas como referencia y respaldo.

#### Objetivo específico y paquete EDT
OE3 · Requisitos 3.0 y 3.1 · EDT 1.5.1 a 1.5.3

#### Valor para el usuario
Reemplaza el cálculo empírico de reabastecimiento (entrevista 1) por un pronóstico basado en datos.

#### Historias de usuario
- HU-19: Entrenar y evaluar el modelo TCN (Must, 8 pts, Sprint 1 → terminada en Sprint 2)
- TT-01: Cargar los datos sintéticos de demostración (seed) (Must, 5 pts, Sprint 1)
- HU-20: Ver el pronóstico de consumo de las próximas semanas (Must, 5 pts, Sprint 2)


#### HU-19: Entrenar y evaluar el modelo TCN

##### Épica
EP-06: Pronóstico de demanda con TCN

##### Historia
**Como** Product Owner
**quiero** un informe que compare el error del modelo TCN con el del promedio móvil de 4 semanas
**para** verificar los indicadores OE3-I1 (MAPE ≤ 25 %) y OE4-I3 antes de usar el modelo

##### Criterios de aceptación (Gherkin)
**Escenario 1: Evaluación**
- **Dado** que el historial de consumo está preparado y el conjunto de prueba se fijó antes de entrenar
- **Cuando** se entrena la TCN y se evalúa en el conjunto de prueba
- **Entonces** se obtiene el MAPE de la TCN y del promedio móvil sobre las mismas semanas

**Escenario 2: Historial insuficiente**
- **Dado** que un tostador tiene menos semanas que el mínimo requerido
- **Cuando** se intenta entrenar
- **Entonces** se documenta que para ese tostador se usará el promedio móvil

##### Trazabilidad
Req. 3.1 · OE3 · EDT 1.5.1.2, 1.5.2.1, 1.5.2.3

##### Prioridad (MoSCoW)
Must

##### Story points
8

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### TT-01: Cargar los datos sintéticos de demostración (seed)

##### Épica
EP-06: Pronóstico de demanda con TCN

##### Historia
**Como** equipo del proyecto
**quiero** cargar en la base de datos los tostadores, proveedores, lotes, historial, compras, recepciones y movimientos generados por ml/generar_datos.py
**para** demostrar el flujo completo y el pronóstico con datos coherentes en las revisiones de sprint y en las sesiones de validación del 14 al 20/11 (plan de contingencia del hito H06a)

##### Criterios de aceptación (Gherkin)
**Escenario 1: Carga completa**
- **Dado** que la base tiene la migración aplicada y existen los CSV en ml/datos_sinteticos/generados
- **Cuando** ejecuto python -m app.seed
- **Entonces** se crean los 4 tostadores con su usuario demo, las cooperativas con cuenta, los directorios, lotes, historial, compras, recepciones y movimientos

**Escenario 2: Idempotencia**
- **Dado** que el seed ya se ejecutó
- **Cuando** lo ejecuto otra vez
- **Entonces** no se duplica ningún registro

**Escenario 3: Coherencia**
- **Dado** que los datos están cargados
- **Cuando** consulto GET /existencias con el usuario demo de T01
- **Entonces** el total coincide con existencias_finales_kg de resumen.json

##### Trazabilidad
Plan de contingencia H06a · OE3 · EDT 1.5.1.2

##### Prioridad (MoSCoW)
Must

##### Story points
5

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-20: Ver el pronóstico de consumo de las próximas semanas

##### Épica
EP-06: Pronóstico de demanda con TCN

##### Historia
**Como** tostador
**quiero** ver cuántos kilos de café verde consumiré en las próximas 4 semanas
**para** anticipar mis compras

##### Criterios de aceptación (Gherkin)
**Escenario 1: Pronóstico con TCN**
- **Dado** que tengo historial suficiente
- **Cuando** abro Pronóstico
- **Entonces** veo el consumo estimado por semana para las próximas 4 semanas junto con mi consumo histórico en un gráfico

**Escenario 2: Respaldo**
- **Dado** que mi historial es insuficiente o el modelo no está disponible
- **Cuando** abro Pronóstico
- **Entonces** veo el pronóstico por promedio móvil y un aviso de qué método se usó

##### Trazabilidad
Req. 3.0 · OE3 · EDT 1.5.3, 1.5.5

##### Prioridad (MoSCoW)
Must

##### Story points
5

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


### EP-07: Recomendaciones de abastecimiento y alertas

#### Descripción
Recomendación explicable de cuánto y cuándo comprar, cruzando el pronóstico con las existencias, la disponibilidad y los tiempos de reposición, y alertas de stock bajo.

#### Objetivo específico y paquete EDT
OE3 · Requisito 3.2 · EDT 1.5.4, 1.5.5

#### Valor para el usuario
Mitiga los quiebres de stock. La decisión final, incluido el proveedor, es siempre del tostador.

#### Historias de usuario
- HU-21: Recibir una recomendación de cuánto y cuándo comprar (Must, 8 pts, Sprint 2)
- HU-22: Recibir alertas de stock bajo y próxima compra (Must, 3 pts, Sprint 2)


#### HU-21: Recibir una recomendación de cuánto y cuándo comprar

##### Épica
EP-07: Recomendaciones de abastecimiento y alertas

##### Historia
**Como** tostador
**quiero** recibir una recomendación de la cantidad y la fecha de mi próxima compra
**para** comprar a tiempo sin quedarme sin café ni sobreabastecerme

##### Criterios de aceptación (Gherkin)
**Escenario 1: Cálculo**
- **Dado** que tengo existencias, un pronóstico semanal y un plazo de entrega del proveedor
- **Cuando** abro Recomendaciones
- **Entonces** veo la fecha límite de compra (cuando las existencias proyectadas no cubran el consumo durante el plazo de entrega) y la cantidad sugerida (consumo pronosticado del plazo de entrega + semanas de cobertura - existencias), redondeada al mínimo de compra

**Escenario 2: Factores visibles**
- **Dado** que veo una recomendación
- **Cuando** abro su detalle
- **Entonces** veo los factores usados: existencias, consumo pronosticado, plazo de entrega, mínimo de compra y método de pronóstico

**Escenario 3: Sin recomendación de proveedor**
- **Dado** que tengo varios proveedores con lotes disponibles
- **Cuando** veo la recomendación
- **Entonces** el sistema no recomienda ni selecciona un proveedor

##### Trazabilidad
Req. 3.2 · OE3 · EDT 1.5.4.1, 1.5.4.2

##### Prioridad (MoSCoW)
Must

##### Story points
8

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-22: Recibir alertas de stock bajo y próxima compra

##### Épica
EP-07: Recomendaciones de abastecimiento y alertas

##### Historia
**Como** tostador
**quiero** ver alertas cuando mis existencias estén por debajo de lo que consumiré antes de la próxima entrega
**para** actuar antes de un quiebre de stock

##### Criterios de aceptación (Gherkin)
**Escenario 1: Alerta de stock bajo**
- **Dado** que mis existencias cubren menos semanas que el plazo de entrega
- **Cuando** abro mi panel
- **Entonces** veo una alerta destacada con las semanas de cobertura restantes

**Escenario 2: Sin alerta**
- **Dado** que mis existencias cubren más que el plazo de entrega más una semana
- **Cuando** abro mi panel
- **Entonces** no se muestra la alerta

##### Trazabilidad
Req. 3.2 · OE3 · EDT 1.5.4.3

##### Prioridad (MoSCoW)
Must

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


### EP-08: Comparación de lotes y desempeño de proveedores

#### Descripción
Comparación de lotes de proveedores vinculados e historial de cumplimiento, sin recomendar un proveedor.

#### Objetivo específico y paquete EDT
OE2, OE3 · Requisito 4.0 · EDT 1.4.4.6, 1.4.5.3

#### Valor para el usuario
Pedido en las entrevistas 1 y 3. Prioridad Should/Could: se construyó en el Sprint 2.

#### Historias de usuario
- HU-23: Comparar lotes de mis proveedores vinculados (Should, 5 pts, Sprint 2)
- HU-24: Ver el cumplimiento histórico de un proveedor (Could, 3 pts, Sprint 2)


#### HU-23: Comparar lotes de mis proveedores vinculados

##### Épica
EP-08: Comparación de lotes y desempeño de proveedores

##### Historia
**Como** tostador
**quiero** comparar lado a lado lotes de distintos proveedores por características, precio y disponibilidad
**para** elegir con información objetiva

##### Criterios de aceptación (Gherkin)
**Escenario 1: Comparación**
- **Dado** que selecciono de 2 a 4 lotes
- **Cuando** hago clic en "Comparar"
- **Entonces** veo una tabla con sus atributos alineados, sin un "recomendado"

##### Trazabilidad
Req. 4.0 · OE2 · EDT 1.4.4.6

##### Prioridad (MoSCoW)
Should

##### Story points
5

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT


#### HU-24: Ver el cumplimiento histórico de un proveedor

##### Épica
EP-08: Comparación de lotes y desempeño de proveedores

##### Historia
**Como** tostador
**quiero** ver qué porcentaje de lo acordado me entregó cada proveedor y con qué puntualidad
**para** evaluar la confiabilidad de mis proveedores

##### Criterios de aceptación (Gherkin)
**Escenario 1: Indicador**
- **Dado** que tengo compras recibidas de un proveedor
- **Cuando** abro su ficha
- **Entonces** veo el % de kilos recibidos vs acordados y el % de entregas a tiempo

##### Trazabilidad
Req. 4.0 · OE3 · EDT 1.4.5.3

##### Prioridad (MoSCoW)
Could

##### Story points
3

##### Definition of Ready
- [x] Tiene criterios de aceptación verificables
- [x] Está estimada y priorizada por el Product Owner
- [x] El contrato de API / diseño de pantalla está definido
- [x] No tiene dependencias bloqueantes
- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT
