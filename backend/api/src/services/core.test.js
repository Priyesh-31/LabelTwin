import test from "node:test";
import assert from "node:assert/strict";
import { AuditLog } from "./audit.js";
import { evaluateImpact } from "./impact.js";
import { labels } from "../data/demo.js";

test("latex material change creates cited actions for each US label", () => {
  const report = evaluateImpact({ field: "material", newValue: "natural_rubber_latex" }, labels);
  assert.equal(report.summary.labels, 4);
  assert.equal(report.summary.requiredActions, 12);
  assert.ok(report.affectedLabels.every(item => item.actions.some(action => action.ruleId === "US-NRL-01")));
});

test("audit hash chain detects changed history", () => {
  const audit = new AuditLog();
  audit.append("Engineer", "change.created", { id: "CO-001" });
  audit.append("QA", "label.reviewed", { id: "LBL-001" });
  assert.equal(audit.verify().valid, true);
  audit.events[0].payload.id = "altered";
  assert.equal(audit.verify().valid, false);
});
