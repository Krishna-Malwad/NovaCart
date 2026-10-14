/* ==========================================================================
   NovaCart — core interactions (cart, wishlist, mobile nav, quantity controls)
   No frameworks. Uses fetch() + JSON against the Flask API routes.
   ========================================================================== */

const NovaCart = (() => {

  function csrfSafeHeaders() {
    return { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" };
  }

  async function postJSON(url, payload) {
    const res = await fetch(url, {
      method: "POST",
      headers: csrfSafeHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    return res.json();
  }

  function updateBadge(id, count) {
    let badge = document.getElementById(id);
    const iconLink = badge ? badge.parentElement : null;
    if (count > 0) {
      if (!badge && iconLink === null) return;
      if (!badge) {
        badge = document.createElement("span");
        badge.className = "badge";
        badge.id = id;
      }
      badge.textContent = count;
    } else if (badge) {
      badge.remove();
    }
  }

  function flashButton(btn, text) {
    const original = btn.textContent;
    btn.textContent = text;
    btn.disabled = true;
    setTimeout(() => {
      btn.textContent = original;
      btn.disabled = false;
    }, 1000);
  }

  async function addToCart(productId, quantity = 1, btn = null) {
    try {
      const data = await postJSON("/cart/add", { product_id: productId, quantity });
      updateBadge("cartBadge", data.cart_count);
      if (btn) flashButton(btn, "Added ✓");
    } catch (e) {
      console.error(e);
    }
  }

  function bindGlobalClicks() {
    document.body.addEventListener("click", async (e) => {
      const target = e.target.closest("[data-action]");
      if (!target) return;

      const action = target.dataset.action;
      const productId = parseInt(target.dataset.productId, 10);

      if (action === "add-to-cart") {
        e.preventDefault();
        await addToCart(productId, 1, target);
      }

      if (action === "buy-now") {
        e.preventDefault();
        await addToCart(productId, 1);
        window.location.href = "/checkout";
      }

      if (action === "toggle-wishlist") {
        e.preventDefault();
        const wasActive = target.classList.contains("active");
        try {
          if (wasActive) {
            const data = await postJSON("/wishlist/remove", { product_id: productId });
            target.classList.remove("active");
            updateBadge("wishlistBadge", data.wishlist_count);
          } else {
            const data = await postJSON("/wishlist/add", { product_id: productId });
            target.classList.add("active");
            updateBadge("wishlistBadge", data.wishlist_count);
          }
        } catch (err) { console.error(err); }
      }

      if (action === "remove-from-wishlist") {
        e.preventDefault();
        const data = await postJSON("/wishlist/remove", { product_id: productId });
        updateBadge("wishlistBadge", data.wishlist_count);
        const card = target.closest(".product-card");
        if (card) card.remove();
      }

      if (action === "move-to-cart") {
        e.preventDefault();
        const data = await postJSON("/wishlist/move-to-cart", { product_id: productId });
        updateBadge("cartBadge", data.cart_count);
        updateBadge("wishlistBadge", data.wishlist_count);
        const card = target.closest(".product-card");
        if (card) card.remove();
      }

      if (action === "remove-from-cart") {
        e.preventDefault();
        const data = await postJSON("/cart/remove", { product_id: productId });
        updateBadge("cartBadge", data.cart_count);
        const row = target.closest(".cart-item");
        if (row) row.remove();
        refreshCartTotals(data.totals);
        maybeShowEmptyCart();
      }

      if (action === "qty-increase" || action === "qty-decrease") {
        e.preventDefault();
        const currentQty = parseInt(target.dataset.qty, 10);
        const newQty = action === "qty-increase" ? currentQty + 1 : currentQty - 1;
        const row = target.closest(".cart-item");

        if (newQty <= 0) {
          const data = await postJSON("/cart/remove", { product_id: productId });
          updateBadge("cartBadge", data.cart_count);
          if (row) row.remove();
          refreshCartTotals(data.totals);
          maybeShowEmptyCart();
          return;
        }

        const data = await postJSON("/cart/update", { product_id: productId, quantity: newQty });
        updateBadge("cartBadge", data.cart_count);
        if (row) {
          row.querySelectorAll("[data-action='qty-increase'], [data-action='qty-decrease']")
            .forEach(b => b.dataset.qty = newQty);
          const qtyDisplay = row.querySelector(".qty-display");
          if (qtyDisplay) qtyDisplay.textContent = newQty;
          // update line total using unit price parsed from cart-item-price span
          const unitPriceEl = row.querySelector(".cart-item-price");
          const unitPrice = parseInt(unitPriceEl.textContent.replace(/[^\d]/g, ""), 10);
          const lineTotalEl = row.querySelector(".line-total");
          if (lineTotalEl) lineTotalEl.textContent = formatCurrency(unitPrice * newQty);
        }
        refreshCartTotals(data.totals);
      }
    });
  }

  function formatCurrency(n) {
    return "₹" + n.toLocaleString("en-IN");
  }

  function refreshCartTotals(totals) {
    if (!totals) return;
    const map = {
      sumSubtotal: totals.subtotal,
      sumGst: totals.gst,
      sumTotal: totals.grand_total,
    };
    Object.entries(map).forEach(([id, val]) => {
      const el = document.getElementById(id);
      if (el) el.textContent = formatCurrency(val);
    });
    const deliveryEl = document.getElementById("sumDelivery");
    if (deliveryEl) deliveryEl.textContent = totals.delivery_fee === 0 ? "FREE" : formatCurrency(totals.delivery_fee);
  }

  function maybeShowEmptyCart() {
    const list = document.getElementById("cartItemsList");
    if (list && list.children.length === 0) {
      window.location.reload();
    }
  }

  function bindMobileNav() {
    const hamburger = document.getElementById("hamburgerBtn");
    const strip = document.getElementById("categoryStrip");
    if (!hamburger || !strip) return;
    hamburger.addEventListener("click", () => {
      strip.style.display = strip.style.display === "flex" ? "none" : "flex";
    });
  }

  function bindProductThumbs() {
    document.querySelectorAll(".pd-thumb").forEach(thumb => {
      thumb.addEventListener("click", () => {
        document.querySelectorAll(".pd-thumb").forEach(t => t.classList.remove("active"));
        thumb.classList.add("active");
        const mainImg = document.getElementById("pdMainImage");
        if (mainImg) mainImg.src = thumb.dataset.image;
      });
    });
  }

  function init() {
    bindGlobalClicks();
    bindMobileNav();
    bindProductThumbs();
  }

  return { init, addToCart };
})();

document.addEventListener("DOMContentLoaded", NovaCart.init);
