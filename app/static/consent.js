// Google Analytics loads only after the visitor clicks Accept. Until then no request
// goes to Google and no analytics cookie is set. The choice is kept in localStorage.
(() => {
  const measurementId = document.documentElement.dataset.gaId;
  const banner = document.querySelector("[data-consent-banner]");
  if (!measurementId || !banner) return;

  const STORAGE_KEY = "analytics-consent";

  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag() { window.dataLayer.push(arguments); };
  gtag("consent", "default", {
    analytics_storage: "denied",
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
  });

  function readChoice() {
    try { return localStorage.getItem(STORAGE_KEY); } catch { return null; }
  }

  function saveChoice(value) {
    try { localStorage.setItem(STORAGE_KEY, value); } catch { /* choice lasts for this page only */ }
  }

  let loaded = false;
  function loadAnalytics() {
    if (loaded) return;
    loaded = true;
    gtag("consent", "update", { analytics_storage: "granted" });
    gtag("js", new Date());
    gtag("config", measurementId);
    const script = document.createElement("script");
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`;
    document.head.append(script);
  }

  function deleteAnalyticsCookies() {
    const host = location.hostname;
    const domains = ["", host, `.${host}`, `.${host.split(".").slice(-2).join(".")}`];
    document.cookie.split(";").map((c) => c.split("=")[0].trim())
      .filter((name) => name === "_ga" || name.startsWith("_ga_"))
      .forEach((name) => domains.forEach((domain) => {
        document.cookie = `${name}=; Max-Age=0; path=/${domain ? `; domain=${domain}` : ""}`;
      }));
  }

  function showBanner() {
    banner.hidden = false;
    banner.querySelector("[data-consent-accept]").focus();
  }

  banner.querySelector("[data-consent-accept]").addEventListener("click", () => {
    saveChoice("granted");
    banner.hidden = true;
    loadAnalytics();
  });

  banner.querySelector("[data-consent-reject]").addEventListener("click", () => {
    saveChoice("denied");
    banner.hidden = true;
    deleteAnalyticsCookies();
    // A reload drops the already-loaded Google script if the visitor withdrew consent.
    if (loaded) location.reload();
  });

  document.querySelectorAll("[data-consent-open]").forEach((button) => {
    button.hidden = false;
    button.addEventListener("click", showBanner);
  });

  const choice = readChoice();
  if (choice === "granted") loadAnalytics();
  else if (choice !== "denied") banner.hidden = false;
})();
