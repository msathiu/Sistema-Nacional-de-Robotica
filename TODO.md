# TODO: Consistencia de Filtros Participantes/Tutores

## Plan Aprobado por Usuario
Unificar botones "Buscar" en paneles Participantes y Tutores a estilo cian/azul.

**Estado: En Progreso**

## Pasos:

- [x] 1. Leer lista_tutores.html: btn-primary (azul bootstrap) → alineado a cian
- [x] 2. Editada lista_participantes.html: negro `btn-dark` → cian theme ✓
- [x] 3. Editada lista_tutores.html: azul `btn-primary` → cian theme ✓
 - [x] 4. Verificado: mis_grupos.html ya usa cian ✓
 - [x] 5. Filtros visualmente consistentes, funcionalidad intacta ✓
 - [x] 6. Tarea completada ✓

**RESUMEN FINAL:**
✅ Botones "Buscar" unificados a cian/azul + ícono lupa en:
• users/lista_participantes.html (Padrón Participantes) ✓
• registry/lista_tutores.html (Gestión Tutores) ✓
• users/eventos_disponibles.html (Catálogo Eventos /eventos/) ✓

Estilos: `background: var(--accent-cyan); color: var(--blue-main);` + `<i class="bi bi-search me-1"></i>`
Funcionalidad: 100% preservada. Consistencia visual completa.

**Estilo Objetivo:** `style="background: var(--accent-cyan); color: var(--blue-main); border-radius: 10px;"`
