# Pantalla del médico

Página estática (HTML + JS, sin servidor) que lee `pedidos.js` (la misma lista que `pedidos.json`, para abrirla con doble clic) y se muestra como un panel dentro de una vista simulada de la historia clínica.

Debe mostrar:
- Los 3 grupos: Empeorando (S3) → Sin seguimiento (S1b) → Prueba pendiente (S1a).
- Por fila: motivo con fecha y valor de origen, pedido preparado, línea de nota, fecha de revisión.
- Aviso «X está hoy en consulta» cuando el paciente tiene cita hoy.
- Botones **Firmar** / **Descartar con motivo**; la decisión queda registrada.
- Pestaña **«Fuera de la lista, y por qué»**.
- Etiqueta visible: «Maqueta · datos sintéticos».
