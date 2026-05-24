/**
 * LUPA — Máscaras + validação client-side (espelha apps/core/validators.py).
 *
 * Uso (Alpine.js):
 *
 *   <input x-data x-mask:document
 *          x-data="{ doc: '' }" x-model="doc"
 *          @input="$el.setCustomValidity(LupaMasks.isValidDoc($el.value) ? '' : 'Documento inválido')">
 *
 * Atalho data-mask:
 *
 *   <input data-mask="cpf">
 *   <input data-mask="cnpj">
 *   <input data-mask="doc">    // aceita CPF (até 11) e CNPJ (12-14)
 *   <input data-mask="phone">
 *
 * Validação é executada onblur e ao submit. Em caso de inválido,
 * o input ganha `aria-invalid="true"` e um <p> de erro abaixo recebe
 * a mensagem (procurar elemento com data-mask-error="<id>").
 */
(function () {
  "use strict";

  const onlyDigits = (s) => (s || "").replace(/\D+/g, "");

  // ── CPF ─────────────────────────────────────────────────
  function formatCPF(value) {
    const d = onlyDigits(value).slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
    if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
    return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
  }

  function isValidCPF(value) {
    const d = onlyDigits(value);
    if (d.length !== 11 || /^(\d)\1{10}$/.test(d)) return false;
    const calc = (slice, factor) => {
      let total = 0;
      for (let i = 0; i < slice.length; i++) total += parseInt(slice[i], 10) * (factor - i);
      const rest = total % 11;
      return rest < 2 ? 0 : 11 - rest;
    };
    return calc(d.slice(0, 9), 10) === parseInt(d[9], 10)
        && calc(d.slice(0, 10), 11) === parseInt(d[10], 10);
  }

  // ── CNPJ ────────────────────────────────────────────────
  function formatCNPJ(value) {
    const d = onlyDigits(value).slice(0, 14);
    if (d.length <= 2) return d;
    if (d.length <= 5) return `${d.slice(0, 2)}.${d.slice(2)}`;
    if (d.length <= 8) return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5)}`;
    if (d.length <= 12) return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8)}`;
    return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
  }

  function isValidCNPJ(value) {
    const d = onlyDigits(value);
    if (d.length !== 14 || /^(\d)\1{13}$/.test(d)) return false;
    const calc = (slice, weights) => {
      let total = 0;
      for (let i = 0; i < slice.length; i++) total += parseInt(slice[i], 10) * weights[i];
      const rest = total % 11;
      return rest < 2 ? 0 : 11 - rest;
    };
    const w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    const w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    return calc(d.slice(0, 12), w1) === parseInt(d[12], 10)
        && calc(d.slice(0, 13), w2) === parseInt(d[13], 10);
  }

  // ── CPF ou CNPJ ─────────────────────────────────────────
  function formatDoc(value) {
    const d = onlyDigits(value);
    return d.length <= 11 ? formatCPF(d) : formatCNPJ(d);
  }

  function isValidDoc(value) {
    const d = onlyDigits(value);
    if (d.length === 11) return isValidCPF(d);
    if (d.length === 14) return isValidCNPJ(d);
    return false;
  }

  // ── Telefone BR ─────────────────────────────────────────
  function formatPhone(value) {
    const d = onlyDigits(value).slice(0, 11);
    if (d.length === 0) return "";
    if (d.length <= 2) return `(${d}`;
    if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
    if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
    return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
  }

  function isValidPhone(value) {
    const d = onlyDigits(value);
    if (d.length !== 10 && d.length !== 11) return false;
    if (d[0] === "0" || d[1] === "0") return false;
    if (d.length === 11 && d[2] !== "9") return false;
    return true;
  }

  // ── Aplicação automática via data-mask=... ───────────────
  const MASKS = {
    cpf:   { format: formatCPF,   valid: isValidCPF,   msg: "CPF inválido. Confira os números.",   maxlength: 14 },
    cnpj:  { format: formatCNPJ,  valid: isValidCNPJ,  msg: "CNPJ inválido. Confira os números.",  maxlength: 18 },
    doc:   { format: formatDoc,   valid: isValidDoc,   msg: "CPF ou CNPJ inválido.",               maxlength: 18 },
    phone: { format: formatPhone, valid: isValidPhone, msg: "Telefone inválido. Use (DD) 9XXXX-XXXX.", maxlength: 15 },
  };

  function showError(input, message) {
    input.setAttribute("aria-invalid", "true");
    const errorEl = document.querySelector(`[data-mask-error="${input.id}"]`);
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.classList.remove("hidden");
    }
    input.classList.add("border-red-400", "dark:border-red-600");
  }

  function clearError(input) {
    input.removeAttribute("aria-invalid");
    const errorEl = document.querySelector(`[data-mask-error="${input.id}"]`);
    if (errorEl) {
      errorEl.textContent = "";
      errorEl.classList.add("hidden");
    }
    input.classList.remove("border-red-400", "dark:border-red-600");
  }

  function attachMask(input) {
    const kind = input.dataset.mask;
    const mask = MASKS[kind];
    if (!mask) return;

    input.setAttribute("inputmode", "numeric");
    input.setAttribute("autocomplete", "off");
    if (!input.maxLength || input.maxLength < 0) input.maxLength = mask.maxlength;

    const reformat = () => {
      const start = input.selectionStart || input.value.length;
      const before = input.value;
      input.value = mask.format(input.value);
      // Tenta preservar caret levando em conta os caracteres não-numéricos
      const after = input.value;
      if (start === before.length) {
        input.setSelectionRange(after.length, after.length);
      }
    };

    const validate = () => {
      if (!input.value) { clearError(input); return; }
      if (mask.valid(input.value)) {
        clearError(input);
      } else {
        showError(input, mask.msg);
      }
    };

    input.addEventListener("input", reformat);
    input.addEventListener("blur", validate);

    // No submit do form pai, bloqueia se inválido (mas não obriga preenchimento — campo opcional fica vazio = ok)
    const form = input.closest("form");
    if (form) {
      form.addEventListener("submit", (e) => {
        if (input.value && !mask.valid(input.value)) {
          e.preventDefault();
          showError(input, mask.msg);
          input.focus();
        }
      });
    }

    if (input.value) reformat();
  }

  function init() {
    document.querySelectorAll("input[data-mask]").forEach(attachMask);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Compatibilidade com HTMX: reataca máscaras após swap de conteúdo
  document.addEventListener("htmx:afterSwap", init);

  // Expõe API pública
  window.LupaMasks = {
    formatCPF, formatCNPJ, formatDoc, formatPhone,
    isValidCPF, isValidCNPJ, isValidDoc, isValidPhone,
    onlyDigits,
  };
})();
