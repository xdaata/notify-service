const $ = (id) => document.getElementById(id);
const STATUSES = ["queued", "processing", "sent", "failed"];

const TEXT = {
    ru: {
        queued: "в очереди",
        processing: "отправляется",
        sent: "отправлено",
        failed: "ошибка",
        hintQueued: "ждёт в очереди",
        hintProcessing: "идёт отправка",
        hintSent: "доставлено в Телеграм",
        hintFailed: "3 попытки, затем в очередь ошибок",
        scope: "по последним 100 событиям",
        colStatus: "Статус",
        colType: "Тип события",
        colId: "ID",
        colTime: "Создано",
        newEvent: "Новое событие",
        type: "Тип события",
        payload: "Данные (JSON)",
        key: "Ключ идемпотентности",
        newKey: "Новый ключ",
        keep: "Не менять ключ после отправки (проверить идемпотентность)",
        create: "Создать событие",
        events: "События",
        offline: "Нет связи с API. Проверь, что контейнер api запущен: docker compose ps",
        empty: "Событий пока нет. Создай первое в форме.",
        live: "обновлено",
        off: "нет связи",
        ago: {s: "с назад", m: "мин назад", h: "ч назад"},
        copy: "Скопировать id",
        copied: "Скопирован id",
        badJson: "Данные должны быть корректным JSON.",
        notObject: 'Данные должны быть JSON-объектом, например {"user_id": 1}.',
        created: "Событие создано",
        reused: "Этот ключ уже использовался. Вернул существующее событие, новое не создано",
        failedReq: "Запрос не удался",
        unreachable: "Нет связи с API. Проверь, что контейнер api запущен.",
        unknown: "неизвестная ошибка",
    },
    en: {
        queued: "queued", processing: "processing", sent: "sent", failed: "failed",
        hintQueued: "waiting in the queue", hintProcessing: "being sent now", hintSent: "delivered to Telegram",
        hintFailed: "3 attempts, then the error queue",
        scope: "based on the latest 100 events",
        colStatus: "Status", colType: "Event type", colId: "ID", colTime: "Created",
        newEvent: "New event", type: "Event type", payload: "Data (JSON)",
        key: "Idempotency key", newKey: "New key",
        keep: "Keep the key after sending (to test idempotency)",
        create: "Create event", events: "Events",
        offline: "Can't reach the API. Check that the api container is running: docker compose ps",
        empty: "No events yet. Create the first one with the form.",
        live: "updated", off: "offline",
        ago: {s: "s ago", m: "m ago", h: "h ago"},
        copy: "Copy full id", copied: "Copied id",
        badJson: "Payload must be valid JSON.",
        notObject: 'Payload must be a JSON object, for example {"user_id": 1}.',
        created: "Event created", reused: "This key was already used. Returned the existing event, no new one",
        failedReq: "Request failed", unreachable: "Can't reach the API. Check that the api container is running.",
        unknown: "unknown error",
    },
};

let lang = "ru";
try {
    lang = localStorage.getItem("lang") || "ru";
} catch {
}
let known = new Set();
let lastEvents = [];
let online = null;

const t = (k) => TEXT[lang][k];
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
}[c]));
// old error messages may contain a bot token inside the telegram url
const redact = (s) => String(s ?? "").replace(/bot\d+:[\w-]+/g, "bot…");
const newKey = () => (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`);

function ago(iso) {
    const s = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
    const a = t("ago");
    if (s < 60) return `${s}${a.s}`;
    if (s < 3600) return `${Math.floor(s / 60)}${a.m}`;
    if (s < 86400) return `${Math.floor(s / 3600)}${a.h}`;
    return new Date(iso).toLocaleDateString(lang === "ru" ? "ru-RU" : "en-GB");
}

function say(text, isError) {
    $("say").textContent = text;
    $("say").className = isError ? "err" : "";
}

function render() {
    const events = lastEvents;
    known = new Set(events.map((e) => e.id));
    for (const s of STATUSES) $("n-" + s).textContent = events.filter((e) => e.status === s).length;
    $("empty").hidden = events.length > 0;
    $("feed").innerHTML = events.map((e) => `
    <li class="row">
      <span class="chip ${esc(e.status)}">${esc(t(e.status) || e.status)}</span>
      <span class="type" title="${esc(e.event_type)}">${esc(e.event_type)}</span>
      <button class="id" data-id="${esc(e.id)}" title="${esc(t("copy"))}">${esc(e.id.slice(0, 8))}</button>
      <span class="time">${esc(ago(e.created_at))}</span>
      ${e.error_message ? `<span class="error" title="${esc(redact(e.error_message))}">${esc(redact(e.error_message))}</span>` : ""}
    </li>`).join("");
}

function showLive() {
    if (online === null) return;
    $("live").className = online ? "live" : "live off";
    $("live").textContent = online ? `${t("live")} ${new Date().toLocaleTimeString()}` : t("off");
    $("banner").hidden = online;
}

function applyLang() {
    document.documentElement.lang = lang;
    $("lang").dataset.lang = lang;
    $("lang").setAttribute("aria-checked", String(lang === "en"));
    for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = t(el.dataset.i18n);
    render();
    showLive();
}

async function load() {
    try {
        const res = await fetch("/events?limit=100");
        if (!res.ok) throw new Error(res.status);
        lastEvents = await res.json();
        online = true;
        render();
    } catch {
        online = false;
    }
    showLive();
}

function detail(body) {
    const d = body && body.detail;
    if (Array.isArray(d)) return d.map((x) => x.msg).join("; ");
    return typeof d === "string" ? d : t("unknown");
}

$("lang").onclick = () => {
    lang = lang === "ru" ? "en" : "ru";
    try {
        localStorage.setItem("lang", lang);
    } catch {
    }
    applyLang();
};

$("key").value = newKey();
$("newkey").onclick = () => ($("key").value = newKey());

$("feed").onclick = async (e) => {
    const btn = e.target.closest(".id");
    if (!btn) return;
    try {
        await navigator.clipboard.writeText(btn.dataset.id);
        say(`${t("copied")} ${btn.dataset.id}`);
    } catch {
        say(btn.dataset.id);
    }
};

$("form").onsubmit = async (e) => {
    e.preventDefault();
    let payload;
    try {
        payload = JSON.parse($("payload").value);
    } catch {
        return say(t("badJson"), true);
    }
    if (payload === null || typeof payload !== "object" || Array.isArray(payload)) {
        return say(t("notObject"), true);
    }

    $("send").disabled = true;
    try {
        const res = await fetch("/events", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({event_type: $("type").value, payload, idempotency_key: $("key").value}),
        });
        const body = await res.json().catch(() => null);
        if (res.ok) {
            const msg = known.has(body.id) ? t("reused") : t("created");
            say(`${msg}: ${body.id.slice(0, 8)}.`);
            if (!$("keep").checked) $("key").value = newKey();
        } else {
            say(`${t("failedReq")} (${res.status}): ${detail(body)}`, true);
        }
    } catch {
        say(t("unreachable"), true);
    } finally {
        $("send").disabled = false;
    }
    load();
};

applyLang();
load();
setInterval(() => {
    if (!document.hidden) load();
}, 2000);
document.addEventListener("visibilitychange", () => {
    if (!document.hidden) load();
});
