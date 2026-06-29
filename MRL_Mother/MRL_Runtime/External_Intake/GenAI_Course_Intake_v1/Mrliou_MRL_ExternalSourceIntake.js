'use strict';

const VALID_SOURCE_TYPES = [
  'external_course_landing_page',
  'external_course_syllabus',
  'external_whitepaper',
  'external_research_paper',
  'external_platform_documentation'
];

const MRL_PROTECTED_NAMES = [
  'MRL_Mother', 'Mrliou_MRL_Runtime', 'Mrliou_FlowAgent', 'Mrliou_FlowComputer',
  'Mrliou_MRL_RuntimeOS', 'Mrliou_MRL_RuntimeBridge', 'Mrliou_MRL_LAW',
  'Mrliou_MRL_Knowledge_Index', 'Mrliou_MRL_System_Reconstruction',
  'MRL_RuntimeOS', 'MRL_Backfill', 'MRL_Mother'
];

/**
 * Validates that the external source does not attempt to use protected MRL naming.
 * @param {string} title - source title
 * @param {string} sourceId - source id
 * @returns {boolean}
 */
function _assertNoMRLNameOverride(title, sourceId) {
  for (const name of MRL_PROTECTED_NAMES) {
    if (title.includes(name) || sourceId.includes(name)) {
      throw new Error(
        `INTAKE_REJECTED: External source attempted to use protected MRL name "${name}". ` +
        `External sources cannot define or claim MRL namespaces.`
      );
    }
  }
  return true;
}

/**
 * Validates that all required fields are present and non-empty.
 * @param {object} metadata
 * @returns {string[]} list of missing fields
 */
function _validateRequiredFields(metadata) {
  const required = ['source_type', 'source_title', 'detected_keywords', 'status'];
  return required.filter(f => !metadata[f] || (Array.isArray(metadata[f]) && metadata[f].length === 0));
}

/**
 * Receives external source metadata, validates, and returns a normalized source object.
 * @param {object} rawMetadata - raw external source metadata object
 * @returns {object} normalized_source_object
 */
function intakeExternalSource(rawMetadata) {
  if (!rawMetadata || typeof rawMetadata !== 'object') {
    return {
      intake_status: 'FAIL',
      error: 'INTAKE_ERROR: rawMetadata must be a non-null object',
      normalized_source_object: null
    };
  }

  const missingFields = _validateRequiredFields(rawMetadata);
  if (missingFields.length > 0) {
    return {
      intake_status: 'FAIL',
      error: `INTAKE_ERROR: Missing required fields: ${missingFields.join(', ')}`,
      normalized_source_object: null
    };
  }

  if (!VALID_SOURCE_TYPES.includes(rawMetadata.source_type)) {
    return {
      intake_status: 'FAIL',
      error: `INTAKE_ERROR: Invalid source_type "${rawMetadata.source_type}". Must be one of: ${VALID_SOURCE_TYPES.join(', ')}`,
      normalized_source_object: null
    };
  }

  if (rawMetadata.status !== 'SOURCE_REF_ONLY') {
    return {
      intake_status: 'FAIL',
      error: `INTAKE_ERROR: External source status must be SOURCE_REF_ONLY, got "${rawMetadata.status}"`,
      normalized_source_object: null
    };
  }

  try {
    _assertNoMRLNameOverride(rawMetadata.source_title, rawMetadata.source_id || '');
  } catch (e) {
    return {
      intake_status: 'FAIL',
      error: e.message,
      normalized_source_object: null
    };
  }

  const normalized_source_object = {
    source_id: rawMetadata.source_id || `MRL-EXT-${Date.now()}`,
    source_type: rawMetadata.source_type,
    source_title: rawMetadata.source_title,
    detected_keywords: Array.isArray(rawMetadata.detected_keywords)
      ? [...rawMetadata.detected_keywords]
      : [],
    status: 'SOURCE_REF_ONLY',
    rule: 'external source cannot define MRL, only be absorbed by MRL',
    intake_date: rawMetadata.intake_date || new Date().toISOString().slice(0, 10),
    version: rawMetadata.version || 'v1',
    normalized_at: new Date().toISOString(),
    absorbed_by: 'MRL_Mother_System'
  };

  return {
    intake_status: 'PASS',
    error: null,
    normalized_source_object
  };
}

module.exports = {
  intakeExternalSource,
  VALID_SOURCE_TYPES,
  MRL_PROTECTED_NAMES
};
