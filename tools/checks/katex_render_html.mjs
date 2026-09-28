// Renders every authored formula into the markup a reader's browser actually paints, with the same
// pinned KaTeX build the formula judge uses. Called only by check_content_overflow.py — that judge
// owns extraction, the version pin and the controls.
//
// displayMode defaults to true and KATEX_DISPLAY_MODE=0 switches it off, because the platform gives
// the two kinds different markup (a display formula is served inside an `overflow-x-auto` wrapper,
// an inline one is a bare span in the paragraph) and the width question has a different answer for
// each. Round 102 measured both halves of that sentence on live pages.
//
// throwOnError is false on purpose: a formula that throws is already owned by
// check_katex_formulas.py, and here it must come back as one defective row, not as a dead sweep.
import { createRequire } from 'module';
import { readFileSync, writeFileSync } from 'fs';

const from = process.env.KATEX_REQUIRE_FROM || `${process.cwd()}/`;
const require = createRequire(/[/\\]$/.test(from) ? from : `${from}/`);
let katex;
try {
  katex = require('katex');
} catch (err) {
  console.log(JSON.stringify({ skip: `katex not resolvable: ${err.message}` }));
  process.exit(2);
}

const items = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const display = process.env.KATEX_DISPLAY_MODE !== '0';
const out = items.map((it) => {
  try {
    return { src: it.src, html: katex.renderToString(it.src, { throwOnError: false, displayMode: display }) };
  } catch (err) {
    return { src: it.src, error: String(err.message).slice(0, 160) };
  }
});
writeFileSync(process.argv[3], JSON.stringify({
  version: require('katex/package.json').version,
  display: display,
  count: out.length,
  items: out,
}));
console.log('ok');
