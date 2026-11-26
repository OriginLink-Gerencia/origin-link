# Historias del piloto de OriginLink

Contraste entre el Project Charter del Equipo 3, versión (3), el backlog del repositorio y los recorridos del frontend. Se incluyen las 24 historias, también HU-12, HU-23 y HU-24, clasificadas como futuras en el backlog. TT-01 se comprueba por separado.

| Historias | Dónde comprobarlas | Resultado observable |
| --- | --- | --- |
| HU-01, HU-02 | Acceso | El alta de una tostadora abre su espacio vacío. El correo duplicado y las credenciales incorrectas producen mensajes diferenciados. La sesión dura ocho horas y se puede cerrar desde la navegación. |
| HU-03, HU-06 | Acceso → Crear cuenta de proveedor / Proveedores → Invitar proveedor | El registro de proveedores es directo. Las invitaciones solo vinculan organizaciones desde sus paneles con sesión iniciada. Caducan a los siete días y se consumen al aceptarlas. |
| HU-04, HU-07 | Panel de cada rol / Vínculos y pedidos → Invitaciones pendientes | Cada tostadora consulta su inventario, compras y catálogo. La cooperativa puede aceptar invitaciones dirigidas al correo de su cuenta y consultar sus tostadoras vinculadas y pedidos propios. Una ruta que requiere otro rol muestra acceso restringido. |
| HU-05 | Proveedores → Registrar proveedor | La tostadora registra nombre, región y contacto, edita el directorio y distingue los estados Sin vincular, Invitado y Vinculado. |
| HU-08, HU-09, HU-10 | Publicar lote → Lotes → Ver ficha | La publicación y sus cambios llegan a las tostadoras vinculadas. El catálogo permite filtrar por proveedor y proceso. La ficha incluye procedencia, altitud, condiciones y fecha de actualización. Un lote de disponibilidad cero figura como agotado en el catálogo. |
| HU-11, HU-12 | Registrar lote manual / Documentos del lote | La tostadora registra lotes privados de proveedores sin vínculo. El proveedor adjunta fichas o muestras a sus lotes publicados y la tostadora vinculada puede descargarlas. |
| HU-13, HU-14, HU-15 | Ver ficha → Registrar compra → Compras y entregas | Se comprueban mínimo y disponibilidad. Una recepción parcial deja saldo pendiente. Cerrar la entrega registra el peso efectivo y la diferencia. El historial se filtra por proveedor. |
| HU-16, HU-17 | Inventario y trazabilidad | Recepciones, consumos, mermas y ajustes alimentan el saldo por lote. El ajuste exige motivo. Los saldos negativos se bloquean y el historial de un lote agotado sigue disponible. |
| HU-18 | Inventario → Importar historial de consumo | CSV y XLSX admiten fecha y kg_consumidos. Se agrupan las filas por semana, se indica cuántas se importaron y un archivo con errores se rechaza entero indicando las filas. |
| HU-19, HU-20 | Pronóstico → Método y evaluación | El informe distingue las cifras documentadas en el Charter y las medidas del modelo local. El gráfico y la tabla muestran cuatro semanas. La selección usa el error de validación de la tostadora y explica el respaldo por promedio móvil. |
| HU-21, HU-22 | Resumen / Pronóstico y reposición | La recomendación considera existencias, consumo, plazo, dos semanas de cobertura y mínimo de compra. Toma los parámetros de la última compra o los valores por defecto. La tostadora elige el proveedor. El resumen muestra cobertura restante y alerta de compra próxima o stock bajo según corresponda. |
| HU-23, HU-24 | Lotes → Comparar lotes / Directorio privado | Comparación de dos a cuatro lotes y consulta de porcentaje de kilos recibidos y porcentaje de entregas a tiempo para compras cerradas. Se distingue un proveedor sin entregas de uno con incumplimientos. |

## Datos y alcance de la comprobación

La semilla de las cuatro tostadoras reproduce los saldos del resumen oficial. Del Valle tiene 12,14 kg, Puerto Barranco 16,78 kg, Andina 28,44 kg y Surco 3,32 kg. Dos entradas de la simulación quedaron fuera del CSV de movimientos por sus fechas de registro. Se recuperaron con el generador original y la semilla 42 para conciliar el piloto: 11 kg para Puerto Barranco el 18 de noviembre y 34,57 kg para Andina el 8 de octubre. El piloto se sitúa el 25 de noviembre de 2026.

El modelo local se puede reproducir con `python scripts/train_pilot.py` y NumPy. Usa el historial sintético completo de las cuatro tostadoras, validación cronológica y un bloque de prueba reservado de seis semanas. Los resultados del Charter corresponden a su propio ensayo.

La demostración persiste el estado en el navegador y las fichas en IndexedDB. Para probar una invitación, ambos roles deben usar el mismo origen y perfil del navegador. La autenticación de servidor, los permisos HTTP 403, el intercambio entre dispositivos y la ejecución del seed de la API requieren integración con el backend.

## Estado de la integración

Los recorridos de las 24 historias tienen una implementación local en React. El acceso principal permite crear cuentas de ambos roles directamente. El panel identifica las invitaciones por el correo de la cuenta aunque la tostadora haya registrado al proveedor con otro ID.

FastAPI solo registra la ruta de salud. Quedan pendientes la implementación de las rutas de registro, login, invitaciones y vínculos del contrato, y su integración con los demás módulos. También falta comprobar con datos persistentes del servidor el aislamiento por organización de HU-04, la carga idempotente de TT-01 y los recorridos entre navegadores. La evaluación de pronóstico visible corresponde a los datos sintéticos del piloto y al informe del Charter.

