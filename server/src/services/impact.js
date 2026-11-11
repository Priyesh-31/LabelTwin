import { rules } from "../data/demo.js";

export function evaluateImpact(change, labels) {
  const latex = change.field === "material" && change.newValue === "natural_rubber_latex";
  const selectedRules = latex ? rules.filter(rule => ["US-NRL-01", "US-UDI-01", "GS1-CHK-01"].includes(rule.id)) : rules.filter(rule => rule.id === "GS1-CHK-01");
  const affected = labels.filter(label => label.market === "US").map(label => ({
    labelId: label.id, sku: label.sku, pack: label.pack, market: label.market, language: label.language,
    actions: selectedRules.filter(rule => rule.market === "ALL" || rule.market === label.market).map(rule => ({ ruleId: rule.id, requirement: rule.requirement, citation: rule.citation, severity: rule.severity }))
  }));
  return { change, affectedLabels: affected, summary: { labels: affected.length, requiredActions: affected.reduce((n, item) => n + item.actions.length, 0), markets: [...new Set(affected.map(x => x.market))] } };
}
