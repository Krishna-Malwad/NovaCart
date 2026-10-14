/* ==========================================================================
   NOVA AI — floating chat widget frontend.
   Talks to POST /api/nova and renders replies + product suggestion cards.
   ========================================================================== */

(function () {
  const toggle = document.getElementById("novaToggle");
  const panel = document.getElementById("novaPanel");
  const closeBtn = document.getElementById("novaClose");
  const form = document.getElementById("novaForm");
  const input = document.getElementById("novaInput");
  const messages = document.getElementById("novaMessages");

  if (!toggle || !panel) return;

  toggle.addEventListener("click", () => {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) input.focus();
  });

  closeBtn.addEventListener("click", () => panel.classList.remove("open"));

  function appendMessage(text, sender) {
    const div = document.createElement("div");
    div.className = `nova-msg nova-msg-${sender}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  function appendTyping() {
    const div = document.createElement("div");
    div.className = "nova-msg nova-msg-bot typing-dots";
    div.innerHTML = "<span></span><span></span><span></span>";
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  function appendProducts(products) {
    if (!products || !products.length) return;
    const wrap = document.createElement("div");
    wrap.className = "nova-msg nova-msg-bot";
    wrap.style.width = "100%";
    wrap.style.maxWidth = "100%";

    products.slice(0, 4).forEach(p => {
      const card = document.createElement("a");
      card.href = `/product/${p.id}`;
      card.className = "nova-product-mini";
      card.innerHTML = `
        <img src="${p.image}" alt="${p.name}">
        <div>
          <div class="npm-name">${p.name}</div>
          <div class="npm-price">₹${p.price.toLocaleString("en-IN")} · ${p.rating}★</div>
        </div>
      `;
      wrap.appendChild(card);
    });

    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    appendMessage(text, "user");
    input.value = "";
    const typingEl = appendTyping();

    try {
      const res = await fetch("/api/nova", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          context_product_id: window.NOVA_CONTEXT_PRODUCT_ID || null,
        }),
      });
      const data = await res.json();
      typingEl.remove();
      appendMessage(data.reply, "bot");
      appendProducts(data.products);
    } catch (err) {
      typingEl.remove();
      appendMessage("Something went wrong reaching NOVA. Please try again.", "bot");
      console.error(err);
    }
  });
})();
