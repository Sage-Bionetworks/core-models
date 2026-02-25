# Sage Schema - Import Guide

## Overview
This directory contains 5 JSON Schema files extracted from the Sage data model diagram for import into CoreModels.

## Entity Schemas

### 1. Organization.schema.json
**Description:** Research institutions, companies, or entities

**Properties:**
- `organization_id` (integer, required) - Unique identifier
- `organization_name` (string, required) - Organization name
- `organization_type` (string) - Type/category
- `city` (string) - Location city
- `state` (string) - Location state/province
- `country` (string) - Location country

### 2. Person.schema.json
**Description:** Individuals affiliated with organizations

**Properties:**
- `person_id` (integer, required) - Unique identifier
- `first_name` (string, required) - First name
- `last_name` (string, required) - Last name
- `email` (string, email format) - Email address
- `organization_id` (integer) - FK to Organization
- `status` (string) - Current status
- `synapse_id` (string) - Synapse platform ID

### 3. PersonRole.schema.json
**Description:** Roles that can be assigned to persons

**Properties:**
- `role_id` (integer, required) - Unique identifier
- `role_name` (string, required) - Role name
- `role_category` (string) - Role classification
- `description` (string) - Role description

### 4. WorkItem.schema.json
**Description:** Hierarchical work items (Program → Project → Study)

**Properties:**
- `work_item_id` (integer, required) - Unique identifier
- `work_item_type` (string, required) - Enum: PROGRAM | PROJECT | STUDY
- `name` (string, required) - Work item name
- `description` (string) - Detailed  description
- `status` (string) - Current status
- `parent_work_item_id` (integer, nullable) - FK to parent WorkItem (hierarchy)
- `primary_org_id` (integer) - FK to primary Organization
- `synapse_id` (string) - Synapse platform ID

**Hierarchy:**
- PROGRAM (top level, parent_work_item_id = null)
  - PROJECT (parent_work_item_id = Program ID)
    - STUDY (parent_work_item_id = Project ID)

### 5. PersonWorkItemRole.schema.json
**Description:** Association table linking persons to work items with roles

**Properties:**
- `assignment_id` (integer, required) - Unique identifier
- `work_item_id` (integer, required) - FK to WorkItem
- `person_id` (integer, required) - FK to Person
- `role_id` (integer, required) - FK to PersonRole
- `organization_id` (integer) - FK to Organization (context)
- `start_date` (date) - Assignment start date
- `end_date` (date, nullable) - Assignment end date (null = ongoing)
- `is_active` (boolean) - Whether assignment is currently active

## Relationships

```
Organization (1) ──< (many) Person
Organization (1) ──< (many) WorkItem (as primary_org)
Organization (1) ──< (many) PersonWorkItemRole

Person (1) ──< (many) PersonWorkItemRole
PersonRole (1) ──< (many) PersonWorkItemRole
WorkItem (1) ──< (many) PersonWorkItemRole
WorkItem (1) ──< (many) WorkItem (self-referential hierarchy)
```

## Manual Import Instructions

### Option 1: Via CoreModels Web Interface

1. Navigate to CoreModels project: `63c223a44f5e43acb8ae92763f08fa86`
2. Create a new space called "Schema - Sage" (or use existing space)
3. For each schema file:
   - Click "Import Schema" or similar import function
   - Upload the JSON Schema file
   - Verify the import was successful

### Option 2: Via API (when service is available)

Use the provided `import_sage_schemas.py` script:

```bash
export COREMODELS_API_TOKEN="your-token-here"
python docs/import_sage_schemas.py
```

### Option 3: Manual Node Creation

If bulk import fails, create nodes manually in CoreModels:

1. Create Type nodes for each entity (Organization, Person, PersonRole, WorkItem, PersonWorkItemRole)
2. For each Type, add Elements (properties) with appropriate data types
3. Create Relations to represent foreign keys:
   - Person → Organization (organization_id)
   - WorkItem → Organization (primary_org_id)
   - WorkItem → WorkItem (parent_work_item_id)
   - PersonWorkItemRole → Person (person_id)
   - PersonWorkItemRole → PersonRole (role_id)
   - PersonWorkItemRole → WorkItem (work_item_id)
   - PersonWorkItemRole → Organization (organization_id)

## Data Types Mapping

| JSON Schema Type | CoreModels Element Type |
|------------------|-------------------------|
| integer | Integer |
| string | String |
| string (format: email) | String (with validation pattern) |
| string (format: date) | Date |
| boolean | Boolean |
| enum | Controlled List/Taxonomy |

## Validation Rules

### Required Fields
- **Organization:** organization_id, organization_name
- **Person:** person_id, first_name, last_name
- **PersonRole:** role_id, role_name
- **WorkItem:** work_item_id, work_item_type, name
- **PersonWorkItemRole:** assignment_id, work_item_id, person_id, role_id

### Enums
- **WorkItem.work_item_type:** Must be one of: PROGRAM, PROJECT, STUDY

### Constraints
- All schemas have `additionalProperties: false` - no extra fields allowed
- Email fields must follow email format pattern
- Date fields must follow ISO 8601 date format (YYYY-MM-DD)

## Import Verification

After import, verify:
1. All 5 Type nodes exist in the "Schema - Sage" space
2. Each Type has the correct number of properties/Elements
3. Required fields are marked as required
4. Data types match the specifications
5. Relationships/Relations are properly established

## Troubleshooting

### Import Errors
- **"Object reference not set"**: API service issue - try again later or use manual method
- **HTTP 405**: Endpoint not available - check API documentation
- **Rate limiting (429)**: Wait a few seconds between imports
- **Schema validation**: Ensure JSON is valid and follows Draft-07 spec

### Common Issues
- Space "Schema - Sage" must exist before import (or use "Main" space)
- API token must have write permissions to the project
- Network connectivity to CoreModels API required

## Files in This Directory

- `Organization.schema.json` - Organization entity schema
- `Person.schema.json` - Person entity schema
- `PersonRole.schema.json` - Role entity schema
- `WorkItem.schema.json` - Work item entity schema (hierarchical)
- `PersonWorkItemRole.schema.json` - Association/junction table schema
- `README.md` - This file
- `../import_sage_schemas.py` - Python import script

## Next Steps

1. Import all 5 schemas into CoreModels
2. Create sample data to test relationships
3. Define additional controlled vocabularies for:
   - Organization types
   - Person statuses
   - Work item statuses
   - Role categories
4. Set up validation rules and constraints
5. Document standard workflows (creating Programs → Projects → Studies)

## Contact

For questions about this schema or import process, contact the CoreModels team or Sage Bionetworks data modeling group.

---

**Version:** 1.0.0  
**Created:** February 25, 2026  
**Source:** Extracted from Sage data model diagram  
**Target Project:** 63c223a44f5e43acb8ae92763f08fa86
