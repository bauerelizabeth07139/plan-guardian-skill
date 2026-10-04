/**
 * Resolve hook that substitutes a stub for the one Harness package the plugin
 * imports, so `index.js` can be exercised outside a running Harness.
 *
 * Only `@deepseek-ai/dsh-skill` is redirected; every other specifier — the
 * `node:` builtins especially — resolves normally.
 */

import { registerHooks } from "node:module";

const STUB_URL = new URL("./stub-dsh-skill.mjs", import.meta.url).href;

registerHooks({
	resolve(specifier, context, nextResolve) {
		if (specifier === "@deepseek-ai/dsh-skill") {
			return { url: STUB_URL, shortCircuit: true };
		}
		return nextResolve(specifier, context);
	},
});
