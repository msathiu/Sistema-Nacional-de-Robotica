// ── SIDEBAR ACTIVE LINK ON SCROLL ──
const sections = document.querySelectorAll('.table-card[id]');
const navLinks = document.querySelectorAll('#sidebar nav a[href^="#"]');

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navLinks.forEach(a => a.classList.remove('active'));
      const active = document.querySelector(`#sidebar nav a[href="#${entry.target.id}"]`);
      if (active) {
        active.classList.add('active');
        active.scrollIntoView({ block: 'nearest' });
      }
    }
  });
}, { rootMargin: '-20% 0px -70% 0px' });

sections.forEach(s => observer.observe(s));

// ── SCROLL TO TOP ──
const scrollBtn = document.getElementById('scrollTop');
window.addEventListener('scroll', () => {
  scrollBtn.classList.toggle('visible', window.scrollY > 400);
});
scrollBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// ── MOBILE SIDEBAR ──
const sidebar = document.getElementById('sidebar');
const toggle = document.getElementById('menuToggle');
toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
document.addEventListener('click', e => {
  if (!sidebar.contains(e.target) && e.target !== toggle) sidebar.classList.remove('open');
});

// ── SIDEBAR SEARCH ──
const searchInput = document.getElementById('sidebarSearch');
searchInput.addEventListener('input', () => {
  const q = searchInput.value.toLowerCase();
  navLinks.forEach(a => {
    const match = a.textContent.toLowerCase().includes(q);
    a.style.display = match ? '' : 'none';
  });
  document.querySelectorAll('#sidebar nav .section-label').forEach(lbl => {
    lbl.style.display = '';
  });
});

// ── SMOOTH SCROLL FOR ANCHOR LINKS ──
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      sidebar.classList.remove('open');
    }
  });
});
