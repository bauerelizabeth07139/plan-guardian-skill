/**
 * Functional check for the host half: the plugin is loaded with `@deepseek-ai/dsh-skill`
 * stubbed, its `apply()` runs against a stand-in Cordis context, and the skill
 * it registers is inspected exactly as the Harness would read it.
 *
 * Run: `node --import ./test/hooks.mjs test/skill.test.mjs`
 */

import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { apply, inject, name } from "../index.js";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const manifest = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8"));

let failed = 0;
async function check(label, body) {
	try {
		const detail = await body();
		console.log(`  PASS  ${label}${detail ? ` — ${detail}` : ""}`);
	} catch (error) {
		failed++;
		console.log(`  FAIL  ${label} — ${error.message}`);
	}
}

console.log(`${manifest.name} plugin behaviour`);

const skillsRoot = join(ROOT, "skills");
const skillNames = existsSync(skillsRoot)
	? readdirSync(skillsRoot, { withFileTypes: true })
			.filter((entry) => entry.isDirectory())
			.map((entry) => entry.name)
	: [];

const providers = [];
const logged = [];
const ctx = {
	skills: {
		registerProvider(factory) {
			providers.push(factory);
		},
	},
	logger: {
		info: (message) => logged.push(message),
		warn: (message) => logged.push(message),
	},
};

await check("apply() registers exactly one skill provider", async () => {
	assert.deepEqual(inject, ["skills"], `unexpected inject ${JSON.stringify(inject)}`);
	apply(ctx);
	assert.equal(providers.length, 1, `expected one provider, got ${providers.length}`);
	return name;
});

await check("the provider lists the bundled skill with Harness-shaped metadata", async () => {
	const provider = providers[0]();
	assert.equal(provider.name, name);
	const list = await provider.list();
	assert.equal(list.length, 1, `expected one skill, got ${list.length}`);
	const candidate = list[0];
	assert.deepEqual(skillNames, [candidate.name], `skills/ holds ${skillNames.join(", ")}`);
	assert.equal(candidate.source, "bundled");
	assert.equal(candidate.rank, 600);
	assert.equal(candidate.invocation?.modelInvocable, true);
	assert.equal(candidate.invocation?.userInvocable, true);
	assert.ok(candidate.description.length > 40, "description is too short to be useful");
	const locator = candidate.locator instanceof URL ? candidate.locator : new URL(candidate.locator);
	assert.ok(existsSync(locator), `${locator} does not exist`);
	assert.equal(candidate.resourceBase?.kind, "directory");
	assert.ok(statSync(candidate.resourceBase.path).isDirectory(), "resourceBase must be a directory");
	return `${candidate.name} rank=${candidate.rank}`;
});

await check("get() returns the skill body without front-matter", async () => {
	const provider = providers[0]();
	const [candidate] = await provider.list();
	const selected = await provider.get({ name: candidate.name });
	assert.ok(selected?.content, "no content returned");
	assert.ok(selected.content.length > 200, `content is ${selected.content.length} chars`);
	assert.ok(!selected.content.startsWith("---"), "front-matter was not stripped");
	assert.match(selected.content, /^#\s/mu, "body has no markdown heading");
	assert.equal(await provider.get({ name: "not-this-skill" }), undefined);
	return `${selected.content.length} chars`;
});

await check("the references the skill cites are shipped next to it", async () => {
	const [, skillName] = [null, skillNames[0]];
	const skillDir = join(skillsRoot, skillName);
	const text = readFileSync(join(skillDir, "SKILL.md"), "utf8");
	const cited = [...text.matchAll(/\]\(\.?\/?((?:references|assets)\/[^)]+)\)/gu)].map((match) => match[1]);
	for (const relative of cited) {
		assert.ok(existsSync(join(skillDir, relative)), `cited resource missing: ${relative}`);
	}
	return cited.length === 0 ? "no cited resources" : `${cited.length} cited resource(s) present`;
});

await check("registration is logged", async () => {
	assert.ok(
		logged.some((message) => message.includes(skillNames[0])),
		`nothing logged about ${skillNames[0]}`,
	);
	return logged.at(-1);
});

console.log(`\n${failed === 0 ? "all checks passed" : `${failed} check(s) failed`}`);
process.exit(failed === 0 ? 0 : 1);
