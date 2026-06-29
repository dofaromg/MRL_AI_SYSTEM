'use strict';

const path = require('path');
const fs = require('fs');
const { intakeExternalSource } = require('./Mrliou_MRL_ExternalSourceIntake');
const { mapKeywordsToCapabilities } = require('./Mrliou_MRL_CapabilityMapper');
const { writeBackfillRecord } = require('./Mrliou_MRL_MotherBackfillWriter');

const INTAKE_DIR = __dirname;
const BACKFILL_DIR = path.resolve(INTAKE_DIR, '../../../MRL_Backfill');

const EXPECTED_FILES = {
  intake_dir: [
    'Mrliou_MRL_ExternalSource_GenAI_Course_Intake_v1.json',
    'Mrliou_MRL_ExternalSource_GenAI_Course_Intake_v1.md',
    'Mrliou_MRL_GenAI_External_To_Mother_Mapping_v1.json',
    'Mrliou_MRL_GenAI_External_To_Mother_Mapping_v1.md',
    'Mrliou_MRL_ExternalSourceIntake.js',
    'Mrliou_MRL_CapabilityMapper.js',
    'Mrliou_MRL_MotherBackfillWriter.js',
    'Mrliou_MRL_IntakeRuntimeTest.js'
  ],
  backfill_dir: [
    'Mrliou_MRL_GenAI_Course_Backfill_Record_v1.json',
    'Mrliou_MRL_GenAI_Course_Backfill_Record_v1.md'
  ]
};

let passCount = 0;
let failCount = 0;
const results = [];

function assert(label, condition, detail) {
  if (condition) {
    passCount++;
    results.push({ label, status: 'PASS', detail: detail || '' });
  } else {
    failCount++;
    results.push({ label, status: 'FAIL', detail: detail || 'Assertion failed' });
  }
}

function runTest() {
  console.log('=== Mrliou_MRL_IntakeRuntimeTest.js ===');
  console.log('Running full Intake → Mapping → Backfill chain test...\n');

  // ─── T1: File existence checks ───────────────────────────────────────────
  console.log('[T1] Checking expected file existence...');
  for (const filename of EXPECTED_FILES.intake_dir) {
    const filePath = path.join(INTAKE_DIR, filename);
    const exists = fs.existsSync(filePath);
    const size = exists ? fs.statSync(filePath).size : 0;
    assert(
      `T1: File exists and non-empty: ${filename}`,
      exists && size > 0,
      exists ? `size=${size}` : 'FILE_NOT_FOUND'
    );
  }
  for (const filename of EXPECTED_FILES.backfill_dir) {
    const filePath = path.join(BACKFILL_DIR, filename);
    const exists = fs.existsSync(filePath);
    const size = exists ? fs.statSync(filePath).size : 0;
    assert(
      `T1: File exists and non-empty: ${filename}`,
      exists && size > 0,
      exists ? `size=${size}` : 'FILE_NOT_FOUND'
    );
  }

  // ─── T2: ExternalSourceIntake module ─────────────────────────────────────
  console.log('[T2] Testing ExternalSourceIntake...');
  const testSourceMetadata = {
    source_id: 'MRL-EXT-GENAI-COURSE-001',
    source_type: 'external_course_landing_page',
    source_title: 'Applied Generative AI for Digital Transformation',
    detected_keywords: [
      'Generative AI', 'Digital Transformation', 'AI Workflow',
      'AI Governance', 'Enterprise AI', 'AI Agent', 'Automation'
    ],
    status: 'SOURCE_REF_ONLY',
    intake_date: '2026-06-29',
    version: 'v1'
  };

  const intakeResult = intakeExternalSource(testSourceMetadata);
  assert('T2: intake_status is PASS', intakeResult.intake_status === 'PASS', intakeResult.error || '');
  assert('T2: normalized_source_object is not null', intakeResult.normalized_source_object !== null, '');
  assert(
    'T2: normalized status is SOURCE_REF_ONLY',
    intakeResult.normalized_source_object && intakeResult.normalized_source_object.status === 'SOURCE_REF_ONLY',
    ''
  );
  assert(
    'T2: absorbed_by is MRL_Mother_System',
    intakeResult.normalized_source_object && intakeResult.normalized_source_object.absorbed_by === 'MRL_Mother_System',
    ''
  );

  // T2 rejection test: external source must not claim MRL name
  const rejectedResult = intakeExternalSource({
    source_id: 'BAD-001',
    source_type: 'external_course_landing_page',
    source_title: 'MRL_Mother new definition course',
    detected_keywords: ['Generative AI'],
    status: 'SOURCE_REF_ONLY'
  });
  assert('T2: MRL name override attempt is rejected', rejectedResult.intake_status === 'FAIL', rejectedResult.error || '');

  // ─── T3: CapabilityMapper module ──────────────────────────────────────────
  console.log('[T3] Testing CapabilityMapper...');
  const mapResult = mapKeywordsToCapabilities(testSourceMetadata.detected_keywords);
  assert('T3: map_status is PASS', mapResult.map_status === 'PASS', mapResult.error || '');
  assert('T3: capability_map is non-empty array', Array.isArray(mapResult.capability_map) && mapResult.capability_map.length > 0, '');
  assert(
    'T3: at least 5 capabilities mapped',
    mapResult.capability_map.length >= 5,
    `mapped=${mapResult.capability_map.length}`
  );
  assert(
    'T3: overlap_level values are valid',
    mapResult.capability_map.every(c => ['COMMON', 'STRUCTURAL', 'UNIQUE_SIMILARITY', 'EVIDENCE_REQUIRED'].includes(c.overlap_level)),
    ''
  );

  // ─── T4: MotherBackfillWriter module ──────────────────────────────────────
  console.log('[T4] Testing MotherBackfillWriter...');
  const normalizedSource = intakeResult.normalized_source_object;
  const writeResult = writeBackfillRecord({
    source_ref: normalizedSource,
    capability_map: mapResult.capability_map,
    unmapped_keywords: mapResult.unmapped_keywords,
    record_filename_base: 'Mrliou_MRL_GenAI_Course_Backfill_Record_v1'
  });

  const writeOk = writeResult.json_file.written || (writeResult.json_file.reason && writeResult.json_file.reason.includes('ADDITIVE_WRITE_BLOCKED'));
  assert(
    'T4: backfill write attempt executed (additive-only enforced)',
    writeOk,
    writeResult.json_file.reason || ''
  );
  assert(
    'T4: backfill_record has sha256',
    writeResult.backfill_record && typeof writeResult.backfill_record.sha256 === 'string' && writeResult.backfill_record.sha256.length === 64,
    writeResult.backfill_record ? `sha256=${writeResult.backfill_record.sha256.slice(0, 16)}...` : 'NO_RECORD'
  );

  // ─── T5: Backfill file validation ─────────────────────────────────────────
  console.log('[T5] Validating backfill output files...');
  const backfillJsonPath = path.join(BACKFILL_DIR, 'Mrliou_MRL_GenAI_Course_Backfill_Record_v1.json');
  const backfillMdPath = path.join(BACKFILL_DIR, 'Mrliou_MRL_GenAI_Course_Backfill_Record_v1.md');

  const jsonExists = fs.existsSync(backfillJsonPath);
  assert('T5: backfill JSON file exists', jsonExists, jsonExists ? '' : 'FILE_NOT_FOUND');

  if (jsonExists) {
    const jsonContent = fs.readFileSync(backfillJsonPath, 'utf8');
    let parsedRecord;
    try {
      parsedRecord = JSON.parse(jsonContent);
    } catch (e) {
      parsedRecord = null;
    }
    assert('T5: backfill JSON is valid JSON', parsedRecord !== null, parsedRecord === null ? 'JSON_PARSE_ERROR' : '');
    if (parsedRecord) {
      assert('T5: backfill JSON has source_ref', !!parsedRecord.source_ref, '');
      assert('T5: backfill JSON has mapped_capabilities', Array.isArray(parsedRecord.mapped_capabilities), '');
      assert('T5: backfill JSON has absorbed_into', Array.isArray(parsedRecord.absorbed_into), '');
      assert('T5: backfill JSON has sha256', typeof parsedRecord.sha256 === 'string' && parsedRecord.sha256.length === 64, '');
      assert('T5: backfill JSON has evidence_level', !!parsedRecord.evidence_level, '');
      assert('T5: backfill JSON has runtime_status', !!parsedRecord.runtime_status, '');
      assert('T5: backfill JSON has created_at', !!parsedRecord.created_at, '');
    }
  }

  const mdExists = fs.existsSync(backfillMdPath);
  assert('T5: backfill MD file exists', mdExists, mdExists ? '' : 'FILE_NOT_FOUND');

  // ─── T6: Source JSON validation ────────────────────────────────────────────
  console.log('[T6] Validating source JSON content...');
  const sourceJsonPath = path.join(INTAKE_DIR, 'Mrliou_MRL_ExternalSource_GenAI_Course_Intake_v1.json');
  if (fs.existsSync(sourceJsonPath)) {
    const sourceContent = JSON.parse(fs.readFileSync(sourceJsonPath, 'utf8'));
    assert('T6: source_type is external_course_landing_page', sourceContent.source_type === 'external_course_landing_page', '');
    assert('T6: status is SOURCE_REF_ONLY', sourceContent.status === 'SOURCE_REF_ONLY', '');
    assert('T6: detected_keywords array has 7 items', Array.isArray(sourceContent.detected_keywords) && sourceContent.detected_keywords.length === 7, '');
    assert('T6: rule field present', !!sourceContent.rule, '');
  }

  // ─── T7: Mapping JSON validation ───────────────────────────────────────────
  console.log('[T7] Validating mapping JSON content...');
  const mappingJsonPath = path.join(INTAKE_DIR, 'Mrliou_MRL_GenAI_External_To_Mother_Mapping_v1.json');
  if (fs.existsSync(mappingJsonPath)) {
    const mappingContent = JSON.parse(fs.readFileSync(mappingJsonPath, 'utf8'));
    assert('T7: mappings array has 8 entries', Array.isArray(mappingContent.mappings) && mappingContent.mappings.length === 8, `count=${mappingContent.mappings ? mappingContent.mappings.length : 0}`);
    assert('T7: all mappings have mrl_target', mappingContent.mappings && mappingContent.mappings.every(m => !!m.mrl_target), '');
    assert('T7: all mappings have overlap_level', mappingContent.mappings && mappingContent.mappings.every(m => !!m.overlap_level), '');
    const requiredTargets = [
      'Mrliou_MRL_Runtime', 'Mrliou_FlowAgent', 'Mrliou_FlowComputer',
      'Mrliou_MRL_RuntimeOS', 'Mrliou_MRL_RuntimeBridge',
      'Mrliou_MRL_System_Reconstruction'
    ];
    const allTargets = mappingContent.mappings ? mappingContent.mappings.map(m => m.mrl_target) : [];
    for (const target of requiredTargets) {
      assert(`T7: mapping contains "${target}"`, allTargets.some(t => t.includes(target.replace('Mrliou_', ''))), `missing: ${target}`);
    }
  }

  // ─── Final Summary ─────────────────────────────────────────────────────────
  const totalTests = passCount + failCount;
  const overallStatus = failCount === 0 ? 'PASS' : 'FAIL';

  console.log('\n=== TEST RESULTS ===');
  for (const r of results) {
    const icon = r.status === 'PASS' ? '✓' : '✗';
    console.log(`  ${icon} [${r.status}] ${r.label}${r.detail ? ' — ' + r.detail : ''}`);
  }

  console.log(`\n=== SUMMARY ===`);
  console.log(`Total: ${totalTests} | PASS: ${passCount} | FAIL: ${failCount}`);
  console.log(`\nRuntime Test: ${overallStatus}`);
  console.log(`\nMRL_GenAI_Intake_Runtime_Backfill:`);
  console.log(`STATUS: DELIVERY_${overallStatus}`);

  return {
    overall_status: overallStatus,
    pass_count: passCount,
    fail_count: failCount,
    total: totalTests,
    results
  };
}

const testOutput = runTest();
process.exit(testOutput.fail_count > 0 ? 1 : 0);
