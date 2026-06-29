'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const BACKFILL_BASE_DIR = path.resolve(__dirname, '../../../MRL_Backfill');

/**
 * Resolves the backfill output directory, creating it if needed.
 * @returns {string} absolute path to backfill dir
 */
function _resolveBackfillDir() {
  if (!fs.existsSync(BACKFILL_BASE_DIR)) {
    fs.mkdirSync(BACKFILL_BASE_DIR, { recursive: true });
  }
  return BACKFILL_BASE_DIR;
}

/**
 * Additive-only file write: refuses to overwrite an existing file.
 * Uses the 'wx' exclusive-create flag to atomically fail if the file already
 * exists, avoiding the TOCTOU race between existsSync and writeFileSync.
 * All I/O errors are caught and returned as FAIL results rather than thrown.
 * @param {string} filePath - absolute path
 * @param {string} content - file content string
 * @returns {{ written: boolean, reason: string }}
 */
function _additiveWrite(filePath, content) {
  try {
    fs.writeFileSync(filePath, content, { encoding: 'utf8', flag: 'wx' });
    return { written: true, reason: 'OK' };
  } catch (err) {
    if (err.code === 'EEXIST') {
      return {
        written: false,
        reason: `ADDITIVE_WRITE_BLOCKED: File already exists at "${filePath}". Cannot overwrite mother body files.`
      };
    }
    return {
      written: false,
      reason: `WRITE_ERROR: ${err.message}`
    };
  }
}

/**
 * Computes SHA256 of a string.
 * @param {string} content
 * @returns {string} hex digest
 */
function computeSha256(content) {
  return crypto.createHash('sha256').update(content, 'utf8').digest('hex');
}

/**
 * Writes mapping results into the MRL mother backfill folder.
 * Generates a backfill_record.json. Additive-only — will not overwrite existing files.
 *
 * @param {object} params
 * @param {object} params.source_ref - normalized source object from ExternalSourceIntake
 * @param {object[]} params.capability_map - mapped capabilities from CapabilityMapper
 * @param {object[]} params.unmapped_keywords - unmapped keywords list
 * @param {string} params.record_filename_base - base name for the backfill record (without extension)
 * @returns {object} write result
 */
function writeBackfillRecord(params) {
  const { source_ref, capability_map, unmapped_keywords, record_filename_base } = params;

  if (!source_ref || !capability_map || !record_filename_base) {
    return {
      write_status: 'FAIL',
      error: 'WRITER_ERROR: source_ref, capability_map, and record_filename_base are required',
      backfill_path: null
    };
  }

  const backfillDir = _resolveBackfillDir();

  const absorbed_into = capability_map.map(c => c.mrl_target);
  const not_absorbed = (unmapped_keywords || []).map(u => u.external_keyword);

  const evidence_level = _computeEvidenceLevel(capability_map);

  const recordContent = {
    backfill_id: `MRL-BF-${record_filename_base}`,
    source_ref: {
      source_id: source_ref.source_id,
      source_type: source_ref.source_type,
      source_title: source_ref.source_title,
      status: source_ref.status
    },
    mapped_capabilities: capability_map.map(c => ({
      external_keyword: c.external_keyword,
      mrl_target: c.mrl_target,
      overlap_level: c.overlap_level
    })),
    absorbed_into,
    not_absorbed,
    evidence_level,
    runtime_status: 'BACKFILL_WRITTEN — 沙盒（當下狀態 2026-06-29）；待實機 MRL_Mother Runtime 驗收',
    created_at: '2026-06-29T00:00:00.000Z',
    sha256: ''
  };

  // SHA256 is computed from the canonical form with the sha256 field absent.
  // To verify: parse the JSON, delete the sha256 key, JSON.stringify, hash, compare.
  const { sha256: _omit, ...recordForHashing } = recordContent;
  const sha256 = computeSha256(JSON.stringify(recordForHashing, null, 2));
  recordContent.sha256 = sha256;

  const finalJson = JSON.stringify(recordContent, null, 2);
  const jsonFilePath = path.join(backfillDir, `${record_filename_base}.json`);
  const jsonResult = _additiveWrite(jsonFilePath, finalJson);

  const mdContent = _generateBackfillMd(recordContent);
  const mdFilePath = path.join(backfillDir, `${record_filename_base}.md`);
  const mdResult = _additiveWrite(mdFilePath, mdContent);

  const jsonOk = jsonResult.written || jsonResult.reason.startsWith('ADDITIVE_WRITE_BLOCKED');
  const mdOk = mdResult.written || mdResult.reason.startsWith('ADDITIVE_WRITE_BLOCKED');
  return {
    write_status: jsonOk && mdOk ? 'PASS' : 'FAIL',
    json_file: { path: jsonFilePath, written: jsonResult.written, reason: jsonResult.reason },
    md_file: { path: mdFilePath, written: mdResult.written, reason: mdResult.reason },
    backfill_record: recordContent,
    backfill_path: backfillDir
  };
}

/**
 * Determines evidence level based on overlap distribution.
 * @param {object[]} capabilityMap
 * @returns {string}
 */
function _computeEvidenceLevel(capabilityMap) {
  const structural = capabilityMap.filter(c => c.overlap_level === 'STRUCTURAL').length;
  const common = capabilityMap.filter(c => c.overlap_level === 'COMMON').length;
  const unique = capabilityMap.filter(c => c.overlap_level === 'UNIQUE_SIMILARITY').length;

  if (structural >= 4) return 'HIGH';
  if (structural + common >= 4) return 'MEDIUM_HIGH';
  if (unique > structural) return 'MEDIUM_SIMILARITY';
  return 'MEDIUM';
}

/**
 * Generates markdown representation of a backfill record.
 * @param {object} record
 * @returns {string}
 */
function _generateBackfillMd(record) {
  const absorbed = record.absorbed_into.map(t => `- ${t}`).join('\n');
  const notAbsorbed = record.not_absorbed.length > 0
    ? record.not_absorbed.map(t => `- ${t}`).join('\n')
    : '*(全部已映射)*';
  const capabilities = record.mapped_capabilities
    .map(c => `| ${c.external_keyword} | ${c.mrl_target} | ${c.overlap_level} |`)
    .join('\n');

  return `# MRL GenAI Course Backfill Record

## Backfill 基本資訊

| 欄位 | 值 |
|------|-----|
| Backfill ID | ${record.backfill_id} |
| Source ID | ${record.source_ref.source_id} |
| Source Title | ${record.source_ref.source_title} |
| Source Status | ${record.source_ref.status} |
| Evidence Level | **${record.evidence_level}** |
| Runtime Status | ${record.runtime_status} |
| Created At | ${record.created_at} |
| SHA256 | \`${record.sha256}\` |

## Mapped Capabilities

| External Keyword | MRL Target | Overlap Level |
|-----------------|------------|---------------|
${capabilities}

## Absorbed Into

${absorbed}

## Not Absorbed

${notAbsorbed}

## 狀態標記

當下狀態（2026-06-29）：Backfill 記錄已建立（沙盒）。外部 GenAI 課程概念已映射至 MRL 母體能力層。
待實機 MRL_Mother Runtime 驗收後方可標記 RUNTIME_VERIFIED。
`;
}

module.exports = {
  writeBackfillRecord,
  computeSha256,
  BACKFILL_BASE_DIR
};
