async function pedir(url, opciones) {
  const respuesta = await fetch(url, opciones);
  if (!respuesta.ok) {
    const texto = await respuesta.text();
    throw new Error(texto || "No se pudo leer la información");
  }
  return respuesta.json();
}

function escapar(texto) {
  return String(texto ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function nombreEstado(estado) {
  const nombres = {
    nativa: "Nativa",
    invasiva: "Invasora",
    introducida: "Introducida",
    desconocido: "Sin clasificar",
  };
  return nombres[estado] || "Sin clasificar";
}

function etiqueta(estado) {
  const limpio = escapar(estado || "desconocido");
  return `<span class="tag ${limpio}">${nombreEstado(limpio)}</span>`;
}

function tarjeta(planta) {
  const foto = planta.fotos && planta.fotos[0];
  const imagen = foto
    ? `<img src="${escapar(foto)}" alt="">`
    : `<div class="sin-foto">Sin foto todavía</div>`;
  const nombre = escapar(planta.common_name_es || "Sin nombre común");
  const cientifico = escapar(planta.scientific_name || "");
  const detalle = escapar(planta.ecological_impact || planta.description || "Abre la ficha para ver más.");
  const tono = Number(planta.id || 0) % 4;
  return `<a class="tarjeta" href="/static/detail.html?id=${planta.id}">
    <article class="tono-${tono}">
      ${imagen}
      <div class="cuerpo">
        <h2>${nombre}</h2>
        <p class="cient">${cientifico}</p>
        ${etiqueta(planta.status)}
        <p class="nota">${detalle}</p>
      </div>
    </article>
  </a>`;
}