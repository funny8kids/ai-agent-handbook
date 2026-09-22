// Renders every authored formula with the same KaTeX build the site's math pipeline is
// aligned to, and reports which ones fail. Called by check_katex_formulas.py — run it only
// through that judge, which owns the formula extraction and the planted counterexample.
//
// katex is resolved from KATEX_REQUIRE_FROM (defaults to the caller's cwd), so the repo needs
// no node_modules of its own; the judge exits loudly when nothing resolves.
import { createRequire } from 'module';
import { readFileSync } from 'fs';

// createRequire needs a filename, or a directory with a trailing separator — a bare directory
// argument reads as a module id and fails with a misleading "Cannot find module 'katex'".
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
const failures = [];
let ok = 0;
items.forEach((it, i) => {
  try {
    katex.renderToString(it.src, { throwOnError: true, displayMode: it.kind === 'display' });
    ok += 1;
  } catch (err) {
    failures.push({ i, msg: String(err.message).slice(0, 180) });
  }
});
console.log(JSON.stringify({
  version: require('katex/package.json').version,
  total: items.length,
  ok,
  failures,
}));
