# ADR-0003: Promedio móvil de 4 semanas como respaldo del modelo TCN

- **Estado:** Aceptada
- **Fecha:** 2026-11-18
- **Responsable:** Victor Cruz (Backend e IA)

## Contexto

La TCN necesita un historial suficiente (al menos 12 semanas de ventana + 4 de horizonte + semanas de
prueba). Algunos tostadores pueden no tenerlo, o el modelo puede fallar al cargarse.

## Decisión

El servicio de pronóstico usa la TCN cuando hay historial suficiente y el modelo está disponible; en
otro caso responde con el promedio móvil de 4 semanas e indica en la respuesta qué método se usó.

## Consecuencias

- La recomendación de compra siempre está disponible (atributo de disponibilidad).
- El mismo promedio móvil es la línea base del indicador OE4-I3.
- La interfaz debe mostrar el método usado como parte de los factores de la recomendación.
