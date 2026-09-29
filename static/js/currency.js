const Currency = (() => {
  const RATES = {
    USD:{rate:1,      code:"USD",locale:"en-US"},
    INR:{rate:83.5,   code:"INR",locale:"en-IN"},
    GBP:{rate:0.79,   code:"GBP",locale:"en-GB"},
    EUR:{rate:0.92,   code:"EUR",locale:"de-DE"},
    CAD:{rate:1.36,   code:"CAD",locale:"en-CA"},
    AUD:{rate:1.53,   code:"AUD",locale:"en-AU"},
    SGD:{rate:1.34,   code:"SGD",locale:"en-SG"},
    AED:{rate:3.67,   code:"AED",locale:"ar-AE"},
    JPY:{rate:149.5,  code:"JPY",locale:"ja-JP"},
    BRL:{rate:4.97,   code:"BRL",locale:"pt-BR"},
    MYR:{rate:4.72,   code:"MYR",locale:"ms-MY"},
    ZAR:{rate:18.6,   code:"ZAR",locale:"en-ZA"},
    NGN:{rate:1550,   code:"NGN",locale:"en-NG"},
    PKR:{rate:278,    code:"PKR",locale:"ur-PK"},
    PHP:{rate:56.5,   code:"PHP",locale:"fil-PH"},
    SAR:{rate:3.75,   code:"SAR",locale:"ar-SA"},
    QAR:{rate:3.64,   code:"QAR",locale:"ar-QA"},
    CNY:{rate:7.24,   code:"CNY",locale:"zh-CN"},
    KRW:{rate:1325,   code:"KRW",locale:"ko-KR"},
    TRY:{rate:32.1,   code:"TRY",locale:"tr-TR"},
    SEK:{rate:10.4,   code:"SEK",locale:"sv-SE"},
    NOK:{rate:10.6,   code:"NOK",locale:"nb-NO"},
    CHF:{rate:0.90,   code:"CHF",locale:"de-CH"},
    NZD:{rate:1.63,   code:"NZD",locale:"en-NZ"},
    ILS:{rate:3.71,   code:"ILS",locale:"he-IL"},
    HKD:{rate:7.82,   code:"HKD",locale:"zh-HK"},
    PLN:{rate:3.98,   code:"PLN",locale:"pl-PL"},
    COP:{rate:3920,   code:"COP",locale:"es-CO"},
    ARS:{rate:870,    code:"ARS",locale:"es-AR"},
    MXN:{rate:17.1,   code:"MXN",locale:"es-MX"},
  };
  const COUNTRY_MAP = {
    india:"INR",bangalore:"INR",mumbai:"INR",delhi:"INR",chennai:"INR",
    hyderabad:"INR",pune:"INR",kolkata:"INR",
    "united kingdom":"GBP",uk:"GBP",london:"GBP",manchester:"GBP",
    germany:"EUR",berlin:"EUR",france:"EUR",paris:"EUR",
    netherlands:"EUR",amsterdam:"EUR",ireland:"EUR",dublin:"EUR",
    spain:"EUR",madrid:"EUR",italy:"EUR",portugal:"EUR",
    canada:"CAD",toronto:"CAD",vancouver:"CAD",
    australia:"AUD",sydney:"AUD",melbourne:"AUD",
    singapore:"SGD",
    uae:"AED",dubai:"AED","abu dhabi":"AED",
    japan:"JPY",tokyo:"JPY",
    brazil:"BRL","sao paulo":"BRL",
    malaysia:"MYR","kuala lumpur":"MYR",
    "south africa":"ZAR",johannesburg:"ZAR","cape town":"ZAR",
    nigeria:"NGN",lagos:"NGN",
    pakistan:"PKR",karachi:"PKR",
    philippines:"PHP",manila:"PHP",
    "saudi arabia":"SAR",riyadh:"SAR",
    qatar:"QAR",doha:"QAR",
    china:"CNY",beijing:"CNY",shanghai:"CNY",
    "south korea":"KRW",seoul:"KRW",
    turkey:"TRY",istanbul:"TRY",
    sweden:"SEK",stockholm:"SEK",
    norway:"NOK",oslo:"NOK",
    switzerland:"CHF",zurich:"CHF",
    "new zealand":"NZD",auckland:"NZD",
    israel:"ILS","tel aviv":"ILS",
    "hong kong":"HKD",
    poland:"PLN",warsaw:"PLN",
    colombia:"COP",bogota:"COP",
    argentina:"ARS","buenos aires":"ARS",
    mexico:"MXN","mexico city":"MXN",
    "united states":"USD",usa:"USD","new york":"USD",
    "san francisco":"USD",seattle:"USD",remote:"USD",
  };

  let cur = RATES["USD"];

  function detect(loc) {
    if (!loc) return "USD";
    const l = loc.toLowerCase();
    for (const [k, code] of Object.entries(COUNTRY_MAP)) {
      if (l.includes(k)) return code;
    }
    return "USD";
  }

  async function init() {
    try {
      const r = await API.get("/profile/");
      const code = detect(r.profile?.location || "");
      cur = RATES[code] || RATES["USD"];
      localStorage.setItem("currency_code", code);
    } catch { cur = RATES["USD"]; }
  }

  function fmt(minUSD, maxUSD) {
    if (!minUSD) return "";
    const conv = v => Math.round(v * cur.rate);
    const fmtN = v => {
      try {
        return new Intl.NumberFormat(cur.locale, {
          style:"currency", currency:cur.code, maximumFractionDigits:0
        }).format(v);
      } catch { return cur.code + " " + v.toLocaleString(); }
    };
    const min = fmtN(conv(minUSD));
    return maxUSD ? min + " – " + fmtN(conv(maxUSD)) + " / yr" : min + " / yr";
  }

  function getCode() { return cur.code; }

  return { init, format: fmt, getCode, detect };
})();
window.Currency = Currency;
