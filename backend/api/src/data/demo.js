export const phrases = {
  "PHR-0142": { id: "PHR-0142", version: "1.0", text: "CAUTION: This product contains natural rubber latex which may cause allergic reactions.", approvedBy: "Regulatory Affairs" }
};

export const labels = [
  { id: "LBL-IV100-UNIT-US", sku: "IVSET-100", product: "Sterile IV Administration Set", pack: "Unit", quantity: 1, market: "US", language: "English", version: "3.2", status: "Approved", gtin: "10850000000017", lot: "LT240918", expiry: "2027-09-30", gate: "PASS", template: "Standard sterile device" },
  { id: "LBL-IV100-BOX-US", sku: "IVSET-100", product: "Sterile IV Administration Set", pack: "Shelf box", quantity: 4, market: "US", language: "English", version: "3.2", status: "Approved", gtin: "10850000000024", lot: "LT240918", expiry: "2027-09-30", gate: "PASS", template: "Standard sterile device" },
  { id: "LBL-IV200-UNIT-US", sku: "IVSET-200", product: "Sterile IV Administration Set with Needle-free Port", pack: "Unit", quantity: 1, market: "US", language: "English", version: "2.8", status: "Approved", gtin: "10850000000031", lot: "LT240921", expiry: "2027-09-30", gate: "PASS", template: "Standard sterile device" },
  { id: "LBL-IV300-UNIT-US", sku: "IVSET-300", product: "Sterile IV Administration Set, Extension", pack: "Unit", quantity: 1, market: "US", language: "English", version: "1.5", status: "Approved", gtin: "10850000000048", lot: "LT240930", expiry: "2027-09-30", gate: "PASS", template: "Standard sterile device" }
];

export const rules = [
  { id: "US-NRL-01", market: "US", title: "Latex caution", condition: "Component material is natural rubber latex", requirement: "Include approved bold latex caution", citation: "21 CFR 801.437", severity: "Mandatory" },
  { id: "US-UDI-01", market: "US", title: "UDI carrier", condition: "Device package label", requirement: "UDI must be present and match the master data", citation: "21 CFR 801.20", severity: "Mandatory" },
  { id: "GS1-CHK-01", market: "ALL", title: "GS1 integrity", condition: "Barcode is present", requirement: "GTIN check digit and printed lot must reconcile", citation: "GS1 General Specifications", severity: "Mandatory" },
  { id: "US-DATE-01", market: "US", title: "Date formatting", condition: "Expiry date appears", requirement: "Use YYYY-MM-DD format", citation: "21 CFR 801.18", severity: "Mandatory" }
];

export const seedChange = { id: "CO-2026-031", title: "Injection port material update", entity: "PORT-01", field: "material", oldValue: "synthetic elastomer", newValue: "natural_rubber_latex", author: "Product Engineering", status: "Draft", createdAt: "2026-11-11T09:30:00.000Z" };
