import crypto from "node:crypto";

export class AuditLog {
  constructor() { this.events = []; }
  append(actor, action, payload = {}) {
    const prevHash = this.events.at(-1)?.hash ?? "0".repeat(64);
    const body = { id: crypto.randomUUID(), timestamp: new Date().toISOString(), actor, action, payload };
    const hash = crypto.createHash("sha256").update(prevHash + JSON.stringify(body)).digest("hex");
    const event = { ...body, prevHash, hash };
    this.events.push(event); return event;
  }
  verify() {
    let previous = "0".repeat(64);
    for (let index = 0; index < this.events.length; index++) {
      const { hash, prevHash, ...body } = this.events[index];
      const expected = crypto.createHash("sha256").update(previous + JSON.stringify(body)).digest("hex");
      if (prevHash !== previous || hash !== expected) return { valid: false, brokenAt: index };
      previous = hash;
    }
    return { valid: true, eventCount: this.events.length, lastHash: previous };
  }
}
