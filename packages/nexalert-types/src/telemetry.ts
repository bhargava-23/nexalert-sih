/**
 * Telemetry envelope schema - TypeScript representation.
 *
 * AUTHORITATIVE SCHEMA: schemas/telemetry-envelope.schema.json
 * This module synchronizes to that schema. Any divergence is a bug.
 *
 * Specification: Document 07, Section 7
 */

export enum TelemetrySource {
  HARDWARE = "HARDWARE",
  SIMULATION = "SIMULATION",
}

export interface Location {
  lat: number;  // -90 to 90
  lon: number;  // -180 to 180
  alt?: number; // undefined = missing (NOT zero)
}

export interface Power {
  battery_voltage?: number;
  solar_current?: number;
  battery_percent?: number;  // 0-100
}

export interface Measurements {
  temperature_c?: number;
  humidity_pct?: number;
  pressure_hpa?: number;
  pm25_ug_m3?: number;
  pm10_ug_m3?: number;
}

export interface Diagnostics {
  self_test_passed?: boolean;
  comm_integrity?: number;  // 0-1
  calibration_valid?: boolean;
  stability_index?: number; // 0-1
  uptime_s?: number;
}

/**
 * Canonical telemetry envelope.
 *
 * Critical invariants (IMPLEMENTATION_CONSTITUTION.md):
 * - measurement_timestamp != received_timestamp (Sec 12)
 * - undefined/null = missing, NOT zero (Sec 3)
 * - source distinguishes HARDWARE from SIMULATION
 */
export interface TelemetryEnvelope {
  telemetry_id: string;
  node_id: string;
  sequence: number;
  measurement_timestamp: string; // ISO 8601 UTC
  received_timestamp: string;     // ISO 8601 UTC, server-assigned
  location: Location;
  measurements: Measurements;
  diagnostics: Diagnostics;
  power: Power;
  source: TelemetrySource;
  schema_version: string;
  auth: Record<string, unknown>;
}
