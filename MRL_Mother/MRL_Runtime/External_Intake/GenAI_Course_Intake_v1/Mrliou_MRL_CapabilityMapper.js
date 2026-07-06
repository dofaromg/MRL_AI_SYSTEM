'use strict';

const KEYWORD_TO_MRL_MAP = {
  'generative ai': {
    mrl_target: 'Mrliou_MRL_Runtime',
    overlap_level: 'STRUCTURAL',
    mrl_description: 'MRL Mother Runtime — execution layer for generative intelligence'
  },
  'ai agent': {
    mrl_target: 'Mrliou_FlowAgent',
    overlap_level: 'STRUCTURAL',
    mrl_description: 'MRL FlowAgent — autonomous agent runtime from absorbed FlowAgent lineage'
  },
  'ai workflow': {
    mrl_target: 'Mrliou_FlowComputer',
    overlap_level: 'COMMON',
    mrl_description: 'MRL FlowComputer — workflow orchestration and computation graph'
  },
  'workflow': {
    mrl_target: 'Mrliou_FlowComputer',
    overlap_level: 'COMMON',
    mrl_description: 'MRL FlowComputer — workflow orchestration and computation graph'
  },
  'rag': {
    mrl_target: 'Mrliou_MRL_Knowledge_Index / Vector Memory',
    overlap_level: 'UNIQUE_SIMILARITY',
    mrl_description: 'MRL Knowledge Index with Vector Memory — retrieval layer for context-aware generation'
  },
  'retrieval': {
    mrl_target: 'Mrliou_MRL_Knowledge_Index / Vector Memory',
    overlap_level: 'UNIQUE_SIMILARITY',
    mrl_description: 'MRL Knowledge Index with Vector Memory — retrieval layer for context-aware generation'
  },
  'ai governance': {
    mrl_target: 'Mrliou_MRL_LAW / AuditSupervisor',
    overlap_level: 'STRUCTURAL',
    mrl_description: 'MRL LAW and AuditSupervisor — governance, policy enforcement, audit trail'
  },
  'governance': {
    mrl_target: 'Mrliou_MRL_LAW / AuditSupervisor',
    overlap_level: 'STRUCTURAL',
    mrl_description: 'MRL LAW and AuditSupervisor — governance, policy enforcement, audit trail'
  },
  'enterprise ai': {
    mrl_target: 'Mrliou_MRL_RuntimeOS',
    overlap_level: 'STRUCTURAL',
    mrl_description: 'MRL RuntimeOS — enterprise-grade AI operating system layer'
  },
  'automation': {
    mrl_target: 'Mrliou_MRL_RuntimeBridge',
    overlap_level: 'COMMON',
    mrl_description: 'MRL RuntimeBridge — automation and integration bridge layer'
  },
  'digital transformation': {
    mrl_target: 'Mrliou_MRL_System_Reconstruction',
    overlap_level: 'UNIQUE_SIMILARITY',
    mrl_description: 'MRL System Reconstruction — systematic re-architecture absorbed by MRL mother'
  }
};

const OVERLAP_LEVELS = ['COMMON', 'STRUCTURAL', 'UNIQUE_SIMILARITY', 'EVIDENCE_REQUIRED'];

/**
 * Maps an array of external keywords to MRL capabilities.
 * @param {string[]} keywords - array of external keywords to map
 * @returns {object} capability_map result object
 */
function mapKeywordsToCapabilities(keywords) {
  if (!Array.isArray(keywords) || keywords.length === 0) {
    return {
      map_status: 'FAIL',
      error: 'MAPPER_ERROR: keywords must be a non-empty array',
      capability_map: null
    };
  }

  const capability_map = [];
  const unmapped = [];

  for (const keyword of keywords) {
    const normalizedKey = keyword.toLowerCase().trim();
    const match = KEYWORD_TO_MRL_MAP[normalizedKey];

    if (match) {
      const existing = capability_map.find(c => c.mrl_target === match.mrl_target);
      if (!existing) {
        capability_map.push({
          external_keyword: keyword,
          mrl_target: match.mrl_target,
          mrl_description: match.mrl_description,
          overlap_level: match.overlap_level
        });
      } else {
        existing.additional_keywords = existing.additional_keywords || [];
        existing.additional_keywords.push(keyword);
      }
    } else {
      unmapped.push({
        external_keyword: keyword,
        mrl_target: null,
        overlap_level: 'EVIDENCE_REQUIRED',
        note: 'No direct MRL mapping found; flagged for evidence review'
      });
    }
  }

  return {
    map_status: 'PASS',
    error: null,
    capability_map,
    unmapped_keywords: unmapped,
    summary: {
      total_keywords: keywords.length,
      mapped: capability_map.length,
      unmapped: unmapped.length,
      overlap_distribution: _computeOverlapDistribution(capability_map)
    }
  };
}

/**
 * Computes distribution of overlap levels in the capability map.
 * @param {object[]} capabilityMap
 * @returns {object}
 */
function _computeOverlapDistribution(capabilityMap) {
  const dist = {};
  for (const level of OVERLAP_LEVELS) {
    dist[level] = capabilityMap.filter(c => c.overlap_level === level).length;
  }
  return dist;
}

module.exports = {
  mapKeywordsToCapabilities,
  KEYWORD_TO_MRL_MAP,
  OVERLAP_LEVELS
};
