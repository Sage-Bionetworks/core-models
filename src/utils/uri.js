// Compose the fully-qualified schema URI used by downstream tools:
//   organizationName-schemaName-semanticVersion
//   (e.g. org.synapse.nf-researchToolsClinicalAssessmentTool-2.0.1)
// Schemas registered without a semantic version omit the trailing
// -version segment, matching how Synapse resolves an unversioned $id.
export function schemaUri(row) {
  const base = `${row.organization_name}-${row.schema_name}`
  return row.semantic_version ? `${base}-${row.semantic_version}` : base
}
