// UI State
let activeCategory = 'all';
let cart = { items: [], total: 0 };

function renderCategories() {
  const cats = ['shirt','pant','tshirt','shoe'];
  const wrap = document.getElementById('categoryButtons');
  if (!wrap) return;
  wrap.innerHTML = '';
  cats.forEach(c => {
    const btn = document.createElement('button');
    btn.className = 'btn btn-outline-dark me-2 mb-2 category-btn';
    btn.textContent = c.toUpperCase();
    btn.onclick = () => { activeCategory = c; renderProducts(); };
    wrap.appendChild(btn);
  });
}

function renderProducts() {
  const list = document.getElementById('productList');
  if (!list) return;
  list.innerHTML = '';
  const cats = activeCategory === 'all' ? Object.keys(products) : [activeCategory];
  cats.forEach(cat => {
    products[cat].forEach(prod => {
      list.appendChild(productCard(cat, prod));
    });
  });
}

function productCard(category, p) {
  const col = document.createElement('div');
  col.className = 'col-6 col-lg-4 mb-4'; // 2 per row (mobile), 3 per row (desktop)

  const card = document.createElement('div');
  card.className = 'card h-100 shadow-sm';

  const img = document.createElement('img');
  img.src = p.img;
  img.className = 'card-img-top';
  img.alt = p.name;

  const body = document.createElement('div');
  body.className = 'card-body d-flex flex-column';

  const h5 = document.createElement('h5');
  h5.className = 'card-title';
  h5.textContent = p.name;

  const price = document.createElement('p');
  price.className = 'card-text mb-2';
  price.textContent = '₹' + p.price;

  // sizes
  const sizesWrap = document.createElement('div');
  sizesWrap.className = 'mb-2';
  (p.sizes || []).forEach(sz => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'btn btn-sm btn-outline-secondary me-1 mb-1 size-btn';
    b.textContent = sz;
    b.onclick = () => {
      [...sizesWrap.querySelectorAll('.size-btn')].forEach(x => x.classList.remove('active'));
      b.classList.add('active');
    };
    sizesWrap.appendChild(b);
  });

  // quantity
  const qtyWrap = document.createElement('div');
  qtyWrap.className = 'input-group input-group-sm mb-2';
  const minus = document.createElement('button'); minus.className='btn btn-outline-secondary'; minus.textContent='-';
  const qty = document.createElement('input'); qty.className='form-control text-center'; qty.value=1;
  const plus = document.createElement('button'); plus.className='btn btn-outline-secondary'; plus.textContent='+';
  minus.onclick = ()=>{ let v=parseInt(qty.value||1); qty.value = Math.max(1, v-1); };
  plus.onclick = ()=>{ let v=parseInt(qty.value||1); qty.value = v+1; };
  qtyWrap.append(minus, qty, plus);

  // Add button with success popup
  const add = document.createElement('button');
  add.className = 'btn btn-dark mt-auto';
  add.textContent = 'Add';
  add.onclick = () => {
    let size = null;
    const active = sizesWrap.querySelector('.size-btn.active');
    if (active) size = active.textContent;
    // validate size selected
    if (p.sizes && p.sizes.length > 0 && !size) {
      alert('Please select size');
      return;
    }
    let q = parseInt(qty.value || 1);
    if (isNaN(q) || q < 1) q = 1;
    const subtotal = p.price * q;
    cart.items.push({id:p.id, category, name:p.name, price:p.price, size, qty:q, subtotal});
    recalc();

    // ===== Small popup =====
    const popup = document.createElement('div');
    popup.textContent = 'Added successfully';
    popup.style.position = 'fixed';
    popup.style.bottom = '20px';
    popup.style.left = '50%';
    popup.style.transform = 'translateX(-50%)';
    popup.style.background = '#28a745';
    popup.style.color = '#fff';
    popup.style.padding = '6px 12px';
    popup.style.borderRadius = '4px';
    popup.style.boxShadow = '0 2px 6px rgba(0,0,0,0.3)';
    popup.style.fontSize = '0.85rem';
    popup.style.zIndex = '9999';
    popup.style.opacity = '0';
    popup.style.transition = 'opacity 0.3s ease';
    document.body.appendChild(popup);

    // fade in
    requestAnimationFrame(()=>{ popup.style.opacity='1'; });

    // fade out and remove after 2 seconds
    setTimeout(()=>{
      popup.style.opacity='0';
      popup.addEventListener('transitionend',()=>popup.remove());
    }, 2000);
  };

  body.append(h5, price, sizesWrap, qtyWrap, add);
  card.append(img, body);
  col.append(card);
  return col;
}

function recalc() {
  cart.total = cart.items.reduce((s, it) => s + it.subtotal, 0);
  const totalSpan = document.getElementById('cartTotal');
  if (totalSpan) totalSpan.textContent = '₹' + cart.total;
  const list = document.getElementById('cartItems');
  if (list) {
    list.innerHTML = '';
    cart.items.forEach((it, idx) => {
      const li = document.createElement('li');
      li.className = 'list-group-item d-flex justify-content-between align-items-center';
      li.textContent = `${it.name} (${it.size || '-'}) x ${it.qty}`;
      const amt = document.createElement('span');
      amt.textContent = '₹' + it.subtotal;
      const rm = document.createElement('button');
      rm.className = 'btn btn-sm btn-outline-danger ms-2';
      rm.textContent = 'X';
      rm.onclick = ()=>{ cart.items.splice(idx,1); recalc(); };
      li.append(amt, rm);
      list.appendChild(li);
    });
  }
}

function goToAddress() {
  if (cart.items.length === 0) {
    alert('Please add some items.');
    return;
  }
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/address';
  const input = document.createElement('input');
  input.type = 'hidden';
  input.name = 'cart_json';
  input.value = JSON.stringify(cart);
  form.appendChild(input);
  document.body.appendChild(form);
  form.submit();
}

document.addEventListener('DOMContentLoaded', ()=>{
  const home = document.getElementById('productList');
  if (home) {
    renderCategories();
    renderProducts();
    recalc();
    // default category buttons row also includes ALL if you want
    const allBtn = document.createElement('button');
    allBtn.className = 'btn btn-dark me-2 mb-2 category-btn';
    allBtn.textContent = 'ALL';
    allBtn.onclick = ()=>{ activeCategory='all'; renderProducts(); };
    document.getElementById('categoryButtons').prepend(allBtn);
  }
});
