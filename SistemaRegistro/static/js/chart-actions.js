/**
 * chart-actions.js
 * Botones de pantalla completa y exportación PNG con valores visibles.
 */
(function () {
    const BTN_STYLE = `
        display:inline-flex;align-items:center;justify-content:center;
        width:28px;height:28px;border-radius:6px;border:1px solid #e2e8f0;
        background:white;cursor:pointer;color:#64748b;transition:all 0.2s;padding:0;
    `;

    function getTitulo(canvas) {
        const card = canvas.closest('.card');
        const h5 = card && card.querySelector('h5');
        return h5 ? h5.innerText.trim() : canvas.id;
    }

    function crearBotones(canvas) {
        if (canvas.dataset.actionsAdded) return;
        canvas.dataset.actionsAdded = '1';

        const wrapper = document.createElement('div');
        wrapper.style.cssText = 'position:absolute;top:8px;right:8px;display:flex;gap:4px;z-index:10;opacity:0;transition:opacity 0.2s;';

        const btnFull = document.createElement('button');
        btnFull.innerHTML = '<i class="bi bi-fullscreen" style="font-size:12px;"></i>';
        btnFull.title = 'Pantalla completa';
        btnFull.style.cssText = BTN_STYLE;
        btnFull.addEventListener('mouseenter', () => btnFull.style.background = '#f1f5f9');
        btnFull.addEventListener('mouseleave', () => btnFull.style.background = 'white');
        btnFull.addEventListener('click', () => {
            const target = canvas.closest('.card') || canvas.parentElement;
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                target.requestFullscreen().then(() => {
                    setTimeout(() => { const c = Chart.getChart(canvas); if (c) c.resize(); }, 100);
                });
            }
        });

        const btnPng = document.createElement('button');
        btnPng.innerHTML = '<i class="bi bi-download" style="font-size:12px;"></i>';
        btnPng.title = 'Descargar PNG con valores';
        btnPng.style.cssText = BTN_STYLE;
        btnPng.addEventListener('mouseenter', () => btnPng.style.background = '#f1f5f9');
        btnPng.addEventListener('mouseleave', () => btnPng.style.background = 'white');
        btnPng.addEventListener('click', () => exportarPNG(canvas));

        wrapper.appendChild(btnFull);
        wrapper.appendChild(btnPng);

        const contenedor = canvas.parentElement;
        if (window.getComputedStyle(contenedor).position === 'static') contenedor.style.position = 'relative';
        contenedor.appendChild(wrapper);

        const card = canvas.closest('.card');
        if (card) {
            card.addEventListener('mouseenter', () => wrapper.style.opacity = '1');
            card.addEventListener('mouseleave', () => wrapper.style.opacity = '0');
        }
    }

    function pintarValores(ctx, chart) {
        const type = chart.config.type;
        const datasets = chart.data.datasets;
        const isHorizontal = chart.options.indexAxis === 'y';

        datasets.forEach((dataset, di) => {
            const meta = chart.getDatasetMeta(di);
            if (meta.hidden) return;

            meta.data.forEach((element, index) => {
                const valor = dataset.data[index];
                if (valor === null || valor === undefined || valor === 0) return;

                const label = typeof valor === 'number' ? valor.toLocaleString('es-VE') : valor;
                ctx.save();
                ctx.font = 'bold 11px Inter, sans-serif';
                ctx.fillStyle = '#1e293b';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';

                if (type === 'bar' && !isHorizontal) {
                    ctx.fillText(label, element.x, element.y - 10);
                } else if (type === 'bar' && isHorizontal) {
                    ctx.textAlign = 'left';
                    ctx.fillText(label, element.x + 6, element.y);
                } else if (type === 'line') {
                    ctx.fillStyle = '#0b2c6d';
                    ctx.fillText(label, element.x, element.y - 12);
                } else if (type === 'doughnut' || type === 'pie') {
                    // Para dona/pie: pintar porcentaje en el centro de cada segmento
                    const total = dataset.data.reduce((a, b) => (a || 0) + (b || 0), 0);
                    const percentage = total > 0 ? ((valor / total) * 100).toFixed(1) + '%' : '0%';
                    const label = percentage;
                    const angle = (element.startAngle + element.endAngle) / 2;
                    const r = (element.innerRadius + element.outerRadius) / 2;
                    const x = element.x + Math.cos(angle) * r;
                    const y = element.y + Math.sin(angle) * r;
                    ctx.fillStyle = 'white';
                    ctx.font = 'bold 10px Inter, sans-serif';
                    ctx.fillText(label, x, y);
                } else if (type === 'radar') {
                    ctx.fillStyle = '#0b2c6d';
                    ctx.font = '10px Inter, sans-serif';
                    ctx.fillText(label, element.x, element.y - 8);
                }
                ctx.restore();
            });
        });
    }

    function exportarPNG(canvas) {
        const chart = Chart.getChart(canvas);
        if (!chart) return;

        const titulo = getTitulo(canvas);
        const fecha = new Date().toLocaleDateString('es-VE', {day:'2-digit', month:'2-digit', year:'numeric'});

        // Canvas temporal con margen para header y valores
        const PADDING = 20;
        const HEADER = 52;
        const tmp = document.createElement('canvas');
        tmp.width = canvas.width + PADDING * 2;
        tmp.height = canvas.height + HEADER + PADDING;

        const ctx = tmp.getContext('2d');

        // Fondo blanco
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, tmp.width, tmp.height);

        // Barra superior institucional
        ctx.fillStyle = '#0b2c6d';
        ctx.fillRect(0, 0, tmp.width, 4);

        // Título
        ctx.fillStyle = '#0b2c6d';
        ctx.font = 'bold 13px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(titulo, PADDING, 26);

        // Subtítulo derecha
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`RNR-PRO · ${fecha}`, tmp.width - PADDING, 26);

        // Separador
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(PADDING, 36);
        ctx.lineTo(tmp.width - PADDING, 36);
        ctx.stroke();

        // Copiar el gráfico renderizado
        ctx.drawImage(canvas, PADDING, HEADER);

        // Pintar los valores encima (offset por el header)
        ctx.save();
        ctx.translate(PADDING, HEADER);
        pintarValores(ctx, chart);
        ctx.restore();

        // Descargar
        const link = document.createElement('a');
        link.download = `${titulo.replace(/[^\w\sáéíóúÁÉÍÓÚñÑ]/g,'').trim().replace(/\s+/g,'_')}_${fecha.replace(/\//g,'-')}.png`;
        link.href = tmp.toDataURL('image/png');
        link.click();
    }

    function init() {
        document.querySelectorAll('canvas').forEach(canvas => {
            if (Chart.getChart(canvas)) crearBotones(canvas);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => setTimeout(init, 600));
    } else {
        setTimeout(init, 600);
    }

    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement) {
            document.querySelectorAll('canvas').forEach(canvas => {
                const c = Chart.getChart(canvas); if (c) c.resize();
            });
        }
    });
})();
