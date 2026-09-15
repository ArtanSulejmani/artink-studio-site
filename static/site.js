(() => {
  const menuButton = document.querySelector('.menu-toggle');
  const menu = document.querySelector('.mobile-nav');
  menuButton?.addEventListener('click', () => { const open = menu.classList.toggle('is-open'); menuButton.setAttribute('aria-expanded', String(open)); });
  menu?.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{menu.classList.remove('is-open');menuButton?.setAttribute('aria-expanded','false')}));
  const notice = document.getElementById('privacy-notice');
  try { if (localStorage.getItem('artink-privacy-notice') !== 'seen') notice.hidden = false; } catch { notice.hidden = false; }
  document.getElementById('privacy-accept')?.addEventListener('click',()=>{try{localStorage.setItem('artink-privacy-notice','seen')}catch{} notice.hidden=true});
  const carousel = document.getElementById('home-slides');
  if (carousel) {
    const panels = [...carousel.querySelectorAll('.hero-panel')];
    const dots = [...carousel.querySelectorAll('.slide-dot')];
    const count = carousel.querySelector('.slide-count');
    let current = 0;
    let timer;
    const setSlide = index => {
      current = (index + panels.length) % panels.length;
      panels.forEach((panel, i) => {
        const active = i === current;
        panel.classList.toggle('is-current', active);
        panel.setAttribute('aria-hidden', String(!active));
        panel.querySelectorAll('a').forEach(link => { link.tabIndex = active ? 0 : -1; });
      });
      dots.forEach((dot, i) => {dot.classList.toggle('is-current', i === current); dot.setAttribute('aria-current', String(i === current));});
      count.textContent = `${String(current + 1).padStart(2, '0')} / ${String(panels.length).padStart(2, '0')}`;
    };
    const play = () => {if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches && !document.hidden) timer = window.setInterval(() => setSlide(current + 1), 6500);};
    const pause = () => window.clearInterval(timer);
    carousel.querySelectorAll('[data-slide-to]').forEach(dot=>dot.addEventListener('click',()=>setSlide(Number(dot.dataset.slideTo))));
    carousel.querySelectorAll('[data-slide-direction]').forEach(button=>button.addEventListener('click',()=>setSlide(current+Number(button.dataset.slideDirection))));
    carousel.addEventListener('mouseenter', pause);carousel.addEventListener('mouseleave', play);
    carousel.addEventListener('focusin', pause);carousel.addEventListener('focusout', event => {if(!carousel.contains(event.relatedTarget)) play();});
    document.addEventListener('visibilitychange', () => {pause();if(!document.hidden)play();});
    play();
  }
  const form = document.getElementById('inquiry-form');
  if (form) {
    const params = new URLSearchParams(location.search);
    for (const [param, field] of [['product','productName'],['quantity','requestedQuantity'],['colour','colour'],['size','size']]) {
      const value = params.get(param);
      if (value && value.length <= 180 && form.elements.namedItem(field)) form.elements.namedItem(field).value = param === 'quantity' ? (/^[1-9]\d{0,5}$/.test(value) ? value : '') : value;
    }
    form.addEventListener('submit', event => {
      if (['localhost','127.0.0.1','[::1]'].includes(location.hostname) || location.protocol === 'file:') {
        event.preventDefault();document.getElementById('local-submit-note').hidden = false;
      }
    });
  }
  const search = document.getElementById('product-search');
  const cards = [...document.querySelectorAll('#catalog-grid .product-card')];
  const filters = [...document.querySelectorAll('.filter')];
  let category = 'all';
  const update = () => {const query=(search?.value||'').trim().toLocaleLowerCase();let visible=0;cards.forEach(card=>{const match=(category==='all'||card.dataset.category===category)&&(!query||card.dataset.search.includes(query));card.hidden=!match;if(match)visible++});document.getElementById('empty-state').hidden=visible>0};
  search?.addEventListener('input',update);
  filters.forEach(button=>button.addEventListener('click',()=>{category=button.dataset.filter;filters.forEach(b=>{const selected=b===button;b.classList.toggle('is-selected',selected);b.setAttribute('aria-pressed',String(selected))});update()}));
  const requestedCategory = new URLSearchParams(location.search).get('category');
  filters.find(b=>b.dataset.filter===requestedCategory)?.click();
  document.querySelectorAll('.thumb').forEach(button=>button.addEventListener('click',()=>{const main=document.getElementById('detail-image');main.src=button.dataset.image;document.querySelectorAll('.thumb').forEach(b=>{const selected=b===button;b.classList.toggle('is-selected',selected);b.setAttribute('aria-pressed',String(selected))})}));
  const selection = document.getElementById('product-selection');
  if (selection) {
    const item = JSON.parse(selection.dataset.product);
    const colourButtons = [...selection.querySelectorAll('[data-color]')];
    const sizeButtons = [...selection.querySelectorAll('[data-size]')];
    let colour = null, size = null, colourLabel = null;
    const refresh = () => {
      const complete = (!colourButtons.length || colour !== null) && (!sizeButtons.length || size !== null);
      const row = complete ? item.stock.find(x =>
        String(x.color || '').trim().toLocaleLowerCase() === String(colour || '').trim().toLocaleLowerCase() &&
        String(x.size || '').trim().toLocaleUpperCase() === String(size || '').trim().toLocaleUpperCase()
      ) : null;
      const qty = row ? Number(row.quantity) : NaN;
      const status = !Number.isFinite(qty) ? item.askStock : qty > 0 ? `${item.inStock} (${qty})` : item.outOfStock;
      const message = document.getElementById('stock-message');
      message.textContent = status;
      message.dataset.status = !Number.isFinite(qty) ? 'unknown' : qty > 0 ? 'available' : 'unavailable';
      const quantityInput = document.getElementById('requested-quantity');
      const count = Number(quantityInput.value);
      const requested = Number.isSafeInteger(count) && count > 0 ? String(count) : '1';
      const details = [`${item.quantityLabel}: ${requested}`, colour ? `${item.selectedColor}: ${colourLabel}` : '', size ? `${item.selectedSize}: ${size}` : ''].filter(Boolean).join('\n');
      const inquiryMessage = `${item.body}\n${details}\n\n${location.origin}${location.pathname}`;
      document.getElementById('quote-link').href = `mailto:artinkstudio.2026@gmail.com?subject=${encodeURIComponent(item.subject)}&body=${encodeURIComponent(inquiryMessage)}`;
      document.getElementById('quote-whatsapp').href = `https://wa.me/38970283590?text=${encodeURIComponent(inquiryMessage)}`;
      const params = new URLSearchParams({product: item.product + (item.code ? ` (${item.code})` : ''), quantity: requested});
      if (colour) params.set('colour', colourLabel);
      if (size) params.set('size', size);
      document.getElementById('quote-form-link').href = `${item.contactPath}?${params}`;
    };
    colourButtons.forEach(button=>button.addEventListener('click',()=>{
      colour=button.dataset.color; colourLabel=button.querySelector('span:last-child')?.textContent || colour;
      colourButtons.forEach(b=>b.setAttribute('aria-pressed',String(b===button))); refresh();
    }));
    sizeButtons.forEach(button=>button.addEventListener('click',()=>{
      size=button.dataset.size; sizeButtons.forEach(b=>b.setAttribute('aria-pressed',String(b===button))); refresh();
    }));
    document.getElementById('requested-quantity').addEventListener('input', refresh);
    refresh();
  }
})();
