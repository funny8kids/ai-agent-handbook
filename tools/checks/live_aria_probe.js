// Live structural-parity probe — run this in the browser (Qoder in-app Browser via the
// browser-use MCP's evaluate_script, or DevTools console) on one published page at a time.
//
// It answers a question a text search cannot: did the reader's browser actually build the
// interactive control? Round 55's check_widget_visibility_live.py proves the component's
// words reach the page; this proves they became an ARIA tablist and rendered formulas.
//
// Feed the output to:  python tools/checks/live_aria_manifest.py --diff live.json
// (live.json = a JSON array of the objects this function returns; URLs come from
// tools/checks/live_aria_manifest.py, never guessed)
//
// Known environment limit, deliberately NOT reported as a defect: mermaid renders lazily,
// so a page whose viewport is 0x0 (in-app Browser panel closed) keeps every diagram in
// aria-busy state. This probe therefore returns both the container count and how many are
// still pending; the judge only fails on a container-count mismatch or on pending > authored.
//
// Ordering constraint, learned the hard way: run this only AFTER the navigation call has
// returned. Issuing it in the same batch as the navigation reads a pre-hydration DOM, where
// the text and ARIA tabs already exist but the mermaid containers have not been appended yet
// (measured: mermaid=0 against 2 authored blocks). `ready` is returned so the judge can void
// such a reading instead of reporting a dropped diagram.
() => {
  const mer = [...document.querySelectorAll('div[class*="group/mermaid"]')];
  const painted = mer.filter((c) => {
    const s = c.querySelector('svg');
    return s && s.querySelectorAll('text').length > 0;
  });
  const body = document.body.innerText;
  return JSON.stringify({
    url: location.href.replace(/\/$/, ''),
    ready: document.readyState,
    textlen: document.body.innerText.length,
    title: document.title,
    tabs: document.querySelectorAll('[role="tab"]').length,
    tabpanels: document.querySelectorAll('[role="tabpanel"]').length,
    katex: document.querySelectorAll('.katex').length,
    katexErr: document.querySelectorAll('.katex-error').length,
    mermaid: mer.length,
    mermaid_unrendered: mer.length - painted.length,
    leak: /\{%|\%}/.test(body),
    viewport: [innerWidth, innerHeight],
    hidden: document.visibilityState !== 'visible',
  });
}
