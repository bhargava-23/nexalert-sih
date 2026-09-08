/**
 * Schema synchronization tests for TypeScript telemetry types.
 *
 * Validates that TypeScript interfaces synchronize with the authoritative JSON Schema.
 *
 * Specification: Document 07, Section 7 + Phase 4 Plan Section 1.3
 * Authoritative Schema: schemas/telemetry-envelope.schema.json
 */

import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import * as fs from 'fs';
import * as path from 'path';
import { TelemetryEnvelope, TelemetrySource, Location, Measurements, Diagnostics, Power } from './telemetry';

describe('Schema Synchronization', () => {
  let ajv: Ajv;
  let schema: any;

  beforeAll(() => {
    // Load authoritative JSON Schema
    const schemaPath = path.resolve(__dirname, '../../../schemas/telemetry-envelope.schema.json');
    schema = JSON.parse(fs.readFileSync(schemaPath, 'utf-8'));

    // Initialize AJV with formats
    ajv = new Ajv();
    addFormats(ajv);
  });

  test('authoritative schema file exists', () => {
    const schemaPath = path.resolve(__dirname, '../../../schemas/telemetry-envelope.schema.json');
    expect(fs.existsSync(schemaPath)).toBe(true);
  });

  test('valid envelope validates against authoritative schema', () => {
    const envelope: TelemetryEnvelope = {
      schema_version: 'telemetry.v1',
      telemetry_id: '01JAAAAAAAAAAAAAAAAAAA0000',
      node_id: 'NODE-001',
      sequence: 42,
      measurement_timestamp: '2026-09-08T10:00:00Z',
      received_timestamp: '2026-09-08T10:00:01Z',
      location: {
        lat: 13.12,
        lon: 77.58,
        alt: 920.0
      },
      measurements: {
        temperature_c: 25.5,
        pm25_ugm3: 45.0
      },
      diagnostics: {
        uptime_s: 1234,
        comm_integrity: 0.95
      },
      power: {
        battery_percent: 85.0
      },
      source: TelemetrySource.HARDWARE,
      auth: {}
    };

    const validate = ajv.compile(schema);
    const valid = validate(envelope);

    expect(valid).toBe(true);
    if (!valid) {
      console.error('Validation errors:', validate.errors);
    }
  });

  test('missing fields validate as undefined/null', () => {
    const envelope: TelemetryEnvelope = {
      schema_version: 'telemetry.v1',
      telemetry_id: '01JAAAAAAAAAAAAAAAAAAA0001',
      node_id: 'NODE-002',
      sequence: 1,
      measurement_timestamp: '2026-09-08T10:00:00Z',
      received_timestamp: '2026-09-08T10:00:01Z',
      location: {
        lat: 0,
        lon: 0,
        alt: undefined  // Missing altitude
      },
      measurements: {
        temperature_c: undefined,
        humidity_pct: undefined
      },
      diagnostics: {},
      power: {},
      source: TelemetrySource.SIMULATION,
      auth: {}
    };

    const validate = ajv.compile(schema);
    const valid = validate(envelope);

    expect(valid).toBe(true);
  });

  test('schema version constant matches', () => {
    expect(schema.properties.schema_version.const).toBe('telemetry.v1');
  });

  test('source enum values match', () => {
    const schemaSourceEnum = schema.properties.source.enum;
    expect(schemaSourceEnum).toContain('HARDWARE');
    expect(schemaSourceEnum).toContain('SIMULATION');
    expect(schemaSourceEnum.length).toBe(2);

    // Verify TypeScript enum matches
    expect(TelemetrySource.HARDWARE).toBe('HARDWARE');
    expect(TelemetrySource.SIMULATION).toBe('SIMULATION');
  });

  test('required fields match', () => {
    const schemaRequired = schema.required;
    const expectedRequired = [
      'schema_version',
      'telemetry_id',
      'node_id',
      'sequence',
      'measurement_timestamp',
      'received_timestamp',
      'location',
      'measurements',
      'diagnostics',
      'power',
      'source'
    ];

    expect(schemaRequired.sort()).toEqual(expectedRequired.sort());
  });

  test('location bounds match', () => {
    const locProps = schema.properties.location.properties;

    expect(locProps.lat.minimum).toBe(-90);
    expect(locProps.lat.maximum).toBe(90);
    expect(locProps.lon.minimum).toBe(-180);
    expect(locProps.lon.maximum).toBe(180);
  });

  test('diagnostics range match', () => {
    const diagProps = schema.properties.diagnostics.properties;

    expect(diagProps.comm_integrity.minimum).toBe(0);
    expect(diagProps.comm_integrity.maximum).toBe(1);
    expect(diagProps.stability_index.minimum).toBe(0);
    expect(diagProps.stability_index.maximum).toBe(1);
  });

  test('telemetry_id pattern documented (ULID)', () => {
    const pattern = schema.properties.telemetry_id.pattern;
    expect(pattern).toBe('^[0-9A-HJKMNP-TV-Z]{26}$');
  });

  test('node_id pattern matches', () => {
    const pattern = schema.properties.node_id.pattern;
    expect(pattern).toBe('^NODE-[0-9]{3,}$');
  });

  test('invalid envelope fails validation', () => {
    const invalidEnvelope = {
      schema_version: 'telemetry.v1',
      telemetry_id: 'INVALID_ULID',  // Invalid pattern
      node_id: 'INVALID',  // Invalid pattern
      sequence: -1,  // Invalid (must be >= 0)
      measurement_timestamp: '2026-09-08T10:00:00Z',
      received_timestamp: '2026-09-08T10:00:01Z',
      location: {
        lat: 100,  // Invalid (out of range)
        lon: 0
      },
      measurements: {},
      diagnostics: {},
      power: {},
      source: 'INVALID_SOURCE',  // Invalid enum
      auth: {}
    };

    const validate = ajv.compile(schema);
    const valid = validate(invalidEnvelope);

    expect(valid).toBe(false);
    expect(validate.errors).toBeTruthy();
  });
});
