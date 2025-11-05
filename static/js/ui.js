document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('btn-asignaciones');
  const panel = document.getElementById('panel-asignaciones');
  if (!btn || !panel) return;
  btn.addEventListener('click', e => {
    e.preventDefault();
    panel.classList.toggle('open');
  });
  // Si quieres que inicie abierto, asegúrate que la sección tenga la clase "open" en el HTML
});
