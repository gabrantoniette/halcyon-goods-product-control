/* =========================================================================
   Halcyon Goods - internal product control, web client
   Talks to the client's own backend (same origin), which relays every call to
   the records API and returns a fixed envelope: {success, status_code,
   message, detail, data}. That envelope is what drives the toasts below.
   ========================================================================= */

const $ = (id) => document.getElementById(id);

/* At or below this quantity an item is flagged for restocking. It is a
   warehouse rule, not an API field, so it is derived here from `stock`. */
const LOW_STOCK_THRESHOLD = 10;

const state = {
  products: [],
  search: '',
  category: 'all',
  availability: 'all',
  sort: 'name-asc',
  // An internal control tool is read as a register, so the table leads and the
  // card grid is the alternative - the opposite of a storefront.
  view: 'table',
  apiBaseUrl: '',
  formMode: 'create',   // 'create' | 'replace' | 'patch'
  editing: null,        // the item being edited, untouched
  pendingDelete: null,
};

const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const moneyCompact = new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 1,
});

/* Three states, derived in one place so the tiles, the filter and the badges
   can never disagree about what "low stock" means. */
function stockState(product) {
  const onHand = Number(product.stock) || 0;
  if (!product.in_stock || onHand === 0) return 'out';
  if (onHand <= LOW_STOCK_THRESHOLD) return 'low';
  return 'in';
}

const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]
));

/* ------------------------------------------------------------------ HTTP */

async function call(path, options = {}) {
  try {
    const response = await fetch(path, options);
    const body = await response.json().catch(() => null);
    if (body && typeof body.success === 'boolean') return body;
    return {
      success: response.ok,
      status_code: response.status,
      message: response.statusText,
      detail: null,
      data: body,
    };
  } catch (error) {
    return {
      success: false,
      status_code: null,
      message: `Could not reach the client server: ${error.message}`,
      detail: null,
      data: null,
    };
  }
}

const json = (body) => ({
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

const api = {
  health: () => call('/api/health'),
  list: () => call('/api/products'),
  create: (name, body) => call(`/api/products/${encodeURIComponent(name)}`, { method: 'POST', ...json(body) }),
  replace: (name, body) => call(`/api/products/${encodeURIComponent(name)}`, { method: 'PUT', ...json(body) }),
  patch: (name, body) => call(`/api/products/${encodeURIComponent(name)}`, { method: 'PATCH', ...json(body) }),
  remove: (name) => call(`/api/products/${encodeURIComponent(name)}`, { method: 'DELETE' }),
};

/* ---------------------------------------------------------------- toasts */

function toast(kind, title, text = '') {
  const element = document.createElement('div');
  element.className = `toast toast--${kind}`;
  element.innerHTML = `
    <span class="toast__glyph" aria-hidden="true">${kind === 'success' ? '✓' : '✕'}</span>
    <div class="toast__body">
      <span class="toast__title">${esc(title)}</span>
      ${text ? `<span class="toast__text">${esc(text)}</span>` : ''}
    </div>`;
  $('toasts').append(element);
  setTimeout(() => {
    element.style.opacity = '0';
    setTimeout(() => element.remove(), 200);
  }, kind === 'success' ? 3200 : 6000);
}

/** Report an envelope from the backend as a toast. */
function report(result, successTitle) {
  if (result.success) {
    toast('success', successTitle, result.message);
  } else {
    toast('error', result.detail || 'Request failed', result.message);
  }
  return result.success;
}

/* ------------------------------------------------------------ derivation */

function visibleProducts() {
  const term = state.search.trim().toLowerCase();

  let list = state.products.filter((product) => {
    if (state.category !== 'all' && product.category !== state.category) return false;
    if (state.availability !== 'all' && stockState(product) !== state.availability) return false;
    if (!term) return true;
    const haystack = [product.name, product.category, ...(product.tags || [])].join(' ').toLowerCase();
    return haystack.includes(term);
  });

  const [key, direction] = state.sort.split('-');
  const sign = direction === 'asc' ? 1 : -1;
  list = list.slice().sort((a, b) => (
    key === 'name'
      ? sign * String(a.name).localeCompare(String(b.name))
      : sign * ((a[key] ?? 0) - (b[key] ?? 0))
  ));

  return list;
}

/* --------------------------------------------------------------- KPI row */

function renderKpis() {
  const products = state.products;
  const total = products.length;
  const counts = { in: 0, low: 0, out: 0 };
  for (const product of products) counts[stockState(product)] += 1;

  const value = products.reduce((sum, product) => sum + (product.price || 0) * (product.stock || 0), 0);
  const rated = products.filter((product) => typeof product.rating === 'number');
  const averageRating = rated.length
    ? rated.reduce((sum, product) => sum + product.rating, 0) / rated.length
    : 0;
  const categories = new Set(products.map((product) => product.category)).size;

  $('kpi-total').textContent = total;
  $('kpi-total-foot').textContent = total
    ? `across ${categories} ${categories === 1 ? 'category' : 'categories'}`
    : '\u00a0';
  $('kpi-instock').textContent = counts.in;
  $('kpi-lowstock').textContent = counts.low;
  $('kpi-lowstock-foot').textContent = `${LOW_STOCK_THRESHOLD} or fewer on hand`;
  $('kpi-outstock').textContent = counts.out;
  $('kpi-value').textContent = total ? moneyCompact.format(value) : '—';
  $('kpi-rating').textContent = rated.length ? averageRating.toFixed(1) : '—';
  $('kpi-rating-foot').textContent = rated.length ? `based on ${rated.length} rated items` : '\u00a0';
}

/* ----------------------------------------------------------------- chart */

/* Horizontal bars, one hue for every bar: the categories are nominal, so
   shading them by size would double-encode the length as colour. Each bar is
   directly labelled with its count, which is why there are no gridlines. */
function renderChart() {
  const chart = $('chart');
  const counts = new Map();
  for (const product of state.products) {
    counts.set(product.category, (counts.get(product.category) || 0) + 1);
  }

  const rows = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  const empty = rows.length === 0;
  $('chart-empty').hidden = !empty;
  chart.hidden = empty;
  if (empty) { chart.innerHTML = ''; return; }

  const max = Math.max(...rows.map(([, count]) => count));
  const total = state.products.length;

  chart.innerHTML = rows.map(([category, count]) => `
    <div class="chart__row" data-category="${esc(category)}" data-count="${count}" data-share="${Math.round((count / total) * 100)}">
      <span class="chart__label" title="${esc(category)}">${esc(category)}</span>
      <div class="chart__track"><div class="chart__bar" style="width:${(count / max) * 100}%"></div></div>
      <span class="chart__value">${count}</span>
    </div>`).join('');
}

function setupChartTooltip() {
  const tip = $('chart-tip');

  $('chart').addEventListener('mousemove', (event) => {
    const row = event.target.closest('.chart__row');
    if (!row) { tip.hidden = true; return; }
    const { category, count, share } = row.dataset;
    tip.textContent = `${category}: ${count} ${count === '1' ? 'item' : 'items'} (${share}% of the register)`;
    tip.hidden = false;
    tip.style.left = `${Math.min(event.clientX + 14, window.innerWidth - tip.offsetWidth - 12)}px`;
    tip.style.top = `${event.clientY - tip.offsetHeight - 10}px`;
  });

  $('chart').addEventListener('mouseleave', () => { tip.hidden = true; });
}

/* ------------------------------------------------------------ list views */

/* Colour is never the only carrier: each state also has a glyph and a word. */
const STOCK_BADGE = {
  in:  ['good',     '✓', 'Available'],
  low: ['warning',  '▲', 'Low stock'],
  out: ['critical', '✕', 'Out of stock'],
};

function stockBadge(product) {
  const [tone, glyph, label] = STOCK_BADGE[stockState(product)];
  return `<span class="badge badge--${tone}"><span class="badge__glyph" aria-hidden="true">${glyph}</span>${label}</span>`;
}

function renderCards(list) {
  $('cards-view').innerHTML = list.map((product) => `
    <article class="product">
      <div class="product__top">
        <h3 class="product__name">${esc(product.name)}</h3>
        <span class="chip">${esc(product.category)}</span>
      </div>
      <span class="product__price">${money.format(product.price || 0)} <small class="product__unit">per unit</small></span>
      <div class="product__meta">
        ${stockBadge(product)}
        <span>${product.stock} on hand</span>
        <span class="rating"><span class="rating__star" aria-hidden="true">★</span>${(product.rating ?? 0).toFixed(1)}</span>
      </div>
      ${(product.tags || []).length
        ? `<div class="product__tags">${product.tags.map((tag) => `<span class="tag">${esc(tag)}</span>`).join('')}</div>`
        : ''}
      <div class="product__actions">
        <button class="link-btn" data-action="replace" data-name="${esc(product.name)}">Edit</button>
        <button class="link-btn" data-action="patch" data-name="${esc(product.name)}">Quick edit</button>
        <button class="link-btn link-btn--danger" data-action="delete" data-name="${esc(product.name)}">Remove</button>
      </div>
    </article>`).join('');
}

function renderTable(list) {
  $('table-body').innerHTML = list.map((product) => `
    <tr class="row--${stockState(product)}">
      <td class="table__name">${esc(product.name)}</td>
      <td>${esc(product.category)}</td>
      <td class="num">${money.format(product.price || 0)}</td>
      <td class="num">${product.stock}</td>
      <td>${stockBadge(product)}</td>
      <td class="num">${(product.rating ?? 0).toFixed(1)}</td>
      <td>
        <div class="table__actions">
          <button class="link-btn" data-action="replace" data-name="${esc(product.name)}">Edit</button>
          <button class="link-btn" data-action="patch" data-name="${esc(product.name)}">Quick edit</button>
          <button class="link-btn link-btn--danger" data-action="delete" data-name="${esc(product.name)}">Remove</button>
        </div>
      </td>
    </tr>`).join('');
}

function renderList() {
  const list = visibleProducts();
  const nothingAtAll = state.products.length === 0;

  $('result-count').textContent = nothingAtAll
    ? ''
    : `Showing ${list.length} of ${state.products.length} registered items`;

  $('empty-state').hidden = list.length > 0;
  $('empty-title').textContent = nothingAtAll ? 'No items registered' : 'No items found';
  $('empty-text').textContent = nothingAtAll
    ? 'Register the first item to start controlling stock.'
    : 'Try adjusting your search or filters.';

  const showCards = state.view === 'cards' && list.length > 0;
  $('cards-view').hidden = !showCards;
  $('table-view').hidden = !(state.view === 'table' && list.length > 0);

  if (showCards) renderCards(list); else renderTable(list);
}

function renderCategoryOptions() {
  const categories = [...new Set(state.products.map((product) => product.category))].sort();

  const select = $('filter-category');
  const current = state.category;
  select.innerHTML = `<option value="all">All</option>${
    categories.map((category) => `<option value="${esc(category)}">${esc(category)}</option>`).join('')}`;
  select.value = categories.includes(current) ? current : 'all';
  state.category = select.value;

  $('category-options').innerHTML = categories
    .map((category) => `<option value="${esc(category)}"></option>`).join('');
}

function renderAll() {
  renderKpis();
  renderChart();
  renderCategoryOptions();
  renderList();
}

/* -------------------------------------------------------------- API load */

function setApiStatus(kind, label) {
  const pill = $('api-status');
  pill.className = `status-pill status-pill--${kind}`;
  pill.querySelector('.status-pill__label').textContent = label;
}

async function loadProducts({ quiet = false } = {}) {
  const views = [$('cards-view'), $('table-view')];
  if (!quiet) views.forEach((view) => view.classList.add('is-refetching'));

  const result = await api.list();

  views.forEach((view) => view.classList.remove('is-refetching'));

  if (!result.success) {
    setApiStatus('offline', 'API offline');
    $('offline-banner').hidden = false;
    $('offline-detail').textContent = result.message;
    return false;
  }

  setApiStatus('online', 'API online');
  $('offline-banner').hidden = true;
  state.products = Array.isArray(result.data) ? result.data : [];
  renderAll();
  return true;
}

async function loadHealth() {
  const health = await api.health();
  if (health.api_base_url) {
    state.apiBaseUrl = health.api_base_url;
    $('api-base-label').textContent = health.api_base_url;
  }
}

/* ------------------------------------------------------------------ form */

const formFields = ['name', 'category', 'price', 'stock', 'rating', 'tags', 'in_stock'];
const inputOf = (field) => $('product-form').elements[field];

function clearErrors() {
  for (const field of formFields) {
    const input = inputOf(field);
    if (input) input.classList.remove('is-invalid');
  }
  document.querySelectorAll('[data-error-for]').forEach((node) => { node.textContent = ''; });
}

function showError(field, message) {
  inputOf(field)?.classList.add('is-invalid');
  const slot = document.querySelector(`[data-error-for="${field}"]`);
  if (slot) slot.textContent = message;
}

function fillForm(product) {
  inputOf('name').value = product?.name ?? '';
  inputOf('category').value = product?.category ?? '';
  inputOf('price').value = product?.price ?? '';
  inputOf('stock').value = product?.stock ?? '';
  inputOf('rating').value = product?.rating ?? '';
  inputOf('tags').value = (product?.tags || []).join(', ');
  inputOf('in_stock').checked = product ? Boolean(product.in_stock) : true;
}

function readForm() {
  return {
    name: inputOf('name').value.trim(),
    category: inputOf('category').value.trim(),
    price: inputOf('price').value.trim(),
    stock: inputOf('stock').value.trim(),
    rating: inputOf('rating').value.trim(),
    tags: inputOf('tags').value.split(',').map((tag) => tag.trim()).filter(Boolean),
    in_stock: inputOf('in_stock').checked,
  };
}

/** Validate and coerce; returns null when something is wrong. */
function validate(raw) {
  clearErrors();
  let valid = true;

  if (!raw.name) { showError('name', 'Item name is required.'); valid = false; }
  if (!raw.category) { showError('category', 'Category is required.'); valid = false; }

  const price = Number(raw.price);
  if (raw.price === '' || Number.isNaN(price) || price < 0) {
    showError('price', 'Enter a price of 0 or more.'); valid = false;
  }

  const stock = Number(raw.stock);
  if (raw.stock === '' || !Number.isInteger(stock) || stock < 0) {
    showError('stock', 'Enter a whole quantity of 0 or more.'); valid = false;
  }

  const rating = Number(raw.rating);
  if (raw.rating === '' || Number.isNaN(rating) || rating < 0 || rating > 5) {
    showError('rating', 'Enter a rating between 0 and 5.'); valid = false;
  }

  // Every operation addresses an item by name, so duplicates would make
  // updates and removals ambiguous.
  const clashes = state.products.some((product) => (
    product.name.toLowerCase() === raw.name.toLowerCase() && product.name !== state.editing?.name
  ));
  if (raw.name && clashes) {
    showError('name', 'An item with this name is already registered.'); valid = false;
  }

  if (!valid) return null;
  return { name: raw.name, category: raw.category, price, stock, rating, tags: raw.tags, in_stock: raw.in_stock };
}

/** For PATCH: keep only what actually changed against the loaded product. */
function changedFields(body) {
  const original = state.editing;
  const changed = {};
  for (const [key, value] of Object.entries(body)) {
    const before = original[key];
    const differs = Array.isArray(value)
      ? value.join(' ') !== (before || []).join(' ')
      : value !== before;
    if (differs) changed[key] = value;
  }
  return changed;
}

function openForm(mode, product = null) {
  state.formMode = mode;
  state.editing = product;

  const titles = {
    create: ['Register item', 'Adds a new item to the internal register.'],
    replace: ['Edit item', 'Every field is rewritten with what you submit.'],
    patch: ['Quick edit', 'Only the fields you change are sent.'],
  };
  const [title, subtitle] = titles[mode];
  $('form-title').textContent = title;
  $('form-sub').textContent = subtitle;
  $('form-submit').textContent = mode === 'create' ? 'Register item' : 'Save changes';
  $('patch-hint').hidden = mode !== 'patch';

  clearErrors();
  fillForm(product);
  $('form-dialog').showModal();
  inputOf('name').focus();
}

async function submitForm(event) {
  event.preventDefault();

  const body = validate(readForm());
  if (!body) return;

  const submit = $('form-submit');
  submit.disabled = true;

  let result;
  if (state.formMode === 'create') {
    result = await api.create(body.name, body);
  } else if (state.formMode === 'replace') {
    result = await api.replace(state.editing.name, body);
  } else {
    const changed = changedFields(body);
    if (Object.keys(changed).length === 0) {
      submit.disabled = false;
      toast('error', 'Nothing changed', 'Adjust at least one field before saving.');
      return;
    }
    result = await api.patch(state.editing.name, changed);
  }

  submit.disabled = false;

  const titles = { create: 'Item registered', replace: 'Item updated', patch: 'Item partially updated' };
  if (report(result, titles[state.formMode])) {
    $('form-dialog').close();
    await loadProducts({ quiet: true });
  }
}

/* ---------------------------------------------------------------- delete */

function openConfirm(product) {
  state.pendingDelete = product;
  $('confirm-text').textContent = `"${product.name}" will be permanently removed from the internal register.`;
  $('confirm-dialog').showModal();
}

async function confirmDelete() {
  const product = state.pendingDelete;
  if (!product) return;

  const button = $('confirm-ok');
  button.disabled = true;
  const result = await api.remove(product.name);
  button.disabled = false;

  $('confirm-dialog').close();
  if (report(result, 'Item removed')) await loadProducts({ quiet: true });
}

/* ----------------------------------------------------------------- theme */

function applyTheme(theme) {
  if (theme) document.documentElement.dataset.theme = theme;
  else delete document.documentElement.dataset.theme;
}

function currentTheme() {
  return document.documentElement.dataset.theme
    || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
}

function toggleTheme() {
  const next = currentTheme() === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  try { localStorage.setItem('halcyon-theme', next); } catch { /* storage may be blocked */ }
}

/* ------------------------------------------------------------------ wire */

function findProduct(name) {
  return state.products.find((product) => product.name === name) || null;
}

function onListClick(event) {
  const button = event.target.closest('[data-action]');
  if (!button) return;

  const product = findProduct(button.dataset.name);
  if (!product) return;

  if (button.dataset.action === 'delete') openConfirm(product);
  else openForm(button.dataset.action, product);
}

function setView(view) {
  state.view = view;
  const isCards = view === 'cards';
  $('view-cards').classList.toggle('is-active', isCards);
  $('view-table').classList.toggle('is-active', !isCards);
  $('view-cards').setAttribute('aria-pressed', String(isCards));
  $('view-table').setAttribute('aria-pressed', String(!isCards));
  renderList();
}

function init() {
  try {
    const saved = localStorage.getItem('halcyon-theme');
    if (saved) applyTheme(saved);
  } catch { /* storage may be blocked */ }

  $('theme-btn').addEventListener('click', toggleTheme);
  $('refresh-btn').addEventListener('click', () => loadProducts());
  $('offline-retry').addEventListener('click', async () => {
    await loadHealth();
    await loadProducts();
  });

  $('search').addEventListener('input', (event) => { state.search = event.target.value; renderList(); });
  $('filter-category').addEventListener('change', (event) => { state.category = event.target.value; renderList(); });
  $('filter-stock').addEventListener('change', (event) => { state.availability = event.target.value; renderList(); });
  $('sort').addEventListener('change', (event) => { state.sort = event.target.value; renderList(); });

  $('view-cards').addEventListener('click', () => setView('cards'));
  $('view-table').addEventListener('click', () => setView('table'));

  $('new-btn').addEventListener('click', () => openForm('create'));
  $('cards-view').addEventListener('click', onListClick);
  $('table-view').addEventListener('click', onListClick);

  $('product-form').addEventListener('submit', submitForm);
  $('confirm-ok').addEventListener('click', confirmDelete);
  document.querySelectorAll('[data-close]').forEach((button) => {
    button.addEventListener('click', () => button.closest('dialog').close());
  });

  setupChartTooltip();

  loadHealth();
  loadProducts();
}

document.addEventListener('DOMContentLoaded', init);
