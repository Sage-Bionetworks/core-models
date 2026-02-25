# Sage Schema Entities - CoreModels Relationship Mapping

## Entity Relationship Diagram

```
┌─────────────────┐
│  ORGANIZATION   │
│  (Type)         │
├─────────────────┤
│ organization_id │ PK
│ organization_...│
│ organization_...│
│ city            │
│ state           │
│ country         │
└────────┬────────┘
         │
         │ (representing)
         │
    ┌────┴──────────────────────────────────┐
    │                                       │
    │                                       │
┌───▼──────────┐                    ┌──────▼──────┐
│    PERSON    │                    │  WORK_ITEM  │
│    (Type)    │                    │   (Type)    │
├──────────────┤                    ├─────────────┤
│ person_id    │ PK                 │ work_item...│ PK
│ first_name   │                    │ work_item...│ PROGRAM|PROJECT|STUDY
│ last_name    │                    │ name        │
│ email        │                    │ description │
│ organizati...│ FK ────────────┐   │ status      │
│ status       │                │   │ parent_wor..│ FK (self) ──┐
│ synapse_id   │                │   │ primary_or..│ FK ─────────┤
└───┬──────────┘                │   │ synapse_id  │             │
    │                           │   └──────┬──────┘             │
    │ (assigned to)             │          │                    │
    │                           │          │ (has assignments)  │
    │       ┌───────────────┐   │          │                    │
    │       │  PERSON_ROLE  │   │          │                    │
    │       │    (Type)     │   │          │                    │
    │       ├───────────────┤   │          │                    │
    │       │ role_id       │ PK│          │                    │
    │       │ role_name     │   │          │                    │
    │       │ role_category │   │          │                    │
    │       │ description   │   │          │                    │
    │       └───┬───────────┘   │          │                    │
    │           │               │          │                    │
    │           │ (serves as)   │          │                    │
    │           │               │          │                    │
    └───────────┴───────────────┴──────────┴────────────────────┘
                                │
                        ┌───────▼──────────────┐
                        │ PERSON_WORKITEM_ROLE │
                        │  (Association Type)  │
                        ├──────────────────────┤
                        │ assignment_id        │ PK
                        │ work_item_id         │ FK → WORK_ITEM
                        │ person_id            │ FK → PERSON
                        │ role_id              │ FK → PERSON_ROLE
                        │ organization_id      │ FK → ORGANIZATION
                        │ start_date           │
                        │ end_date             │
                        │ is_active            │
                        └──────────────────────┘
```

## CoreModels Implementation Guide

### 1. Create Type Nodes

In CoreModels project `63c223a44f5e43acb8ae92763f08fa86`, create 5 Type nodes:

1. **Organization**
2. **Person**
3. **PersonRole**
4. **WorkItem**
5. **PersonWorkItemRole**

### 2. Add Elements to Each Type

#### Organization Elements
| Element Label | Data Type | Required | Description |
|---------------|-----------|----------|-------------|
| organization_id | Integer | Yes | Primary key |
| organization_name | String | Yes | Organization name |
| organization_type | String | No | Type/category |
| city | String | No | City location |
| state | String | No | State/province |
| country | String | No | Country |

#### Person Elements
| Element Label | Data Type | Required | Description |
|---------------|-----------|----------|-------------|
| person_id | Integer | Yes | Primary key |
| first_name | String | Yes | First name |
| last_name | String | Yes | Last name |
| email | String | No | Email address |
| organization_id | Integer | No | FK to Organization |
| status | String | No | Person status |
| synapse_id | String | No | Synapse ID |

#### PersonRole Elements
| Element Label | Data Type | Required | Description |
|---------------|-----------|----------|-------------|
| role_id | Integer | Yes | Primary key |
| role_name | String | Yes | Role name |
| role_category | String | No | Role category |
| description | String | No | Role description |

#### WorkItem Elements
| Element Label | Data Type | Required | Description |
|---------------|-----------|----------|-------------|
| work_item_id | Integer | Yes | Primary key |
| work_item_type | String (Enum) | Yes | PROGRAM/PROJECT/STUDY |
| name | String | Yes | Work item name |
| description | String | No | Description |
| status | String | No | Status |
| parent_work_item_id | Integer | No | FK to parent WorkItem |
| primary_org_id | Integer | No | FK to Organization |
| synapse_id | String | No | Synapse ID |

#### PersonWorkItemRole Elements
| Element Label | Data Type | Required | Description |
|---------------|-----------|----------|-------------|
| assignment_id | Integer | Yes | Primary key |
| work_item_id | Integer | Yes | FK to WorkItem |
| person_id | Integer | Yes | FK to Person |
| role_id | Integer | Yes | FK to PersonRole |
| organization_id | Integer | No | FK to Organization |
| start_date | Date | No | Start date |
| end_date | Date | No | End date |
| is_active | Boolean | No | Active flag |

### 3. Create Relations

Use CoreModels "Domain Includes" and "Range Includes" relations to link types:

#### Relation: "representing" (Organization → Person)
- **From:** Organization
- **To:** Person
- **Description:** Organization represents/employs Person
- **Multiplicity:** 1 Organization → Many Persons

#### Relation: "primary org" (Organization → WorkItem)
- **From:** WorkItem
- **To:** Organization
- **Description:** WorkItem has primary Organization
- **Multiplicity:** 1 WorkItem → 1 Organization

#### Relation: "parent hierarchy" (WorkItem → WorkItem)
- **From:** WorkItem (child)
- **To:** WorkItem (parent)
- **Description:** Self-referential hierarchy (Study → Project → Program)
- **Multiplicity:** 1 WorkItem → 0-1 Parent WorkItem

#### Relation: "assigned to" (Person → PersonWorkItemRole)
- **From:** PersonWorkItemRole
- **To:** Person
- **Description:** Assignment links to Person
- **Multiplicity:** Many Assignments → 1 Person

#### Relation: "has role" (PersonRole → PersonWorkItemRole)
- **From:** PersonWorkItemRole
- **To:** PersonRole
- **Description:** Assignment has Role
- **Multiplicity:** Many Assignments → 1 Role

#### Relation: "works on" (WorkItem → PersonWorkItemRole)
- **From:** PersonWorkItemRole
- **To:** WorkItem
- **Description:** Assignment for WorkItem
- **Multiplicity:** Many Assignments → 1 WorkItem

#### Relation: "org context" (Organization → PersonWorkItemRole)
- **From:** PersonWorkItemRole
- **To:** Organization
- **Description:** Assignment in Organization context
- **Multiplicity:** Many Assignments → 1 Organization

### 4. Create Controlled Vocabularies

#### work_item_type Taxonomy
Create a Taxonomy node with List items:
- PROGRAM
- PROJECT
- STUDY

Link to WorkItem.work_item_type using "Controlled List" relation.

#### Suggested Additional Taxonomies
- **organization_type:** Academic, Industry, Government, Non-profit
- **person_status:** Active, Inactive, Alumni
- **work_item_status:** Planning, Active, Completed, On Hold, Cancelled
- **role_category:** Leadership, Research, Administration, Technical

### 5. WorkItem Hierarchy Rules

The parent_work_item_id creates a 3-level hierarchy:

```
PROGRAM (level 1)
  ├─ parent_work_item_id: null
  │
  ├─ PROJECT (level 2)
  │    ├─ parent_work_item_id: <PROGRAM.work_item_id>
  │    │
  │    ├─ STUDY (level 3)
  │         └─ parent_work_item_id: <PROJECT.work_item_id>
  │
  └─ PROJECT (level 2)
       └─ STUDY (level 3)
```

**Validation Rules:**
- PROGRAM must have parent_work_item_id = null
- PROJECT must have parent_work_item_id pointing to a PROGRAM
- STUDY must have parent_work_item_id pointing to a PROJECT

### 6. Sample Data Flow

#### Creating a Program with Team
1. Create ORGANIZATION: "Sage Bionetworks"
2. Create PERSON: "John Doe" (organization_id → Sage)
3. Create PERSON_ROLE: "Principal Investigator"
4. Create WORK_ITEM (PROGRAM): "ALS Research Initiative" (primary_org_id → Sage, parent = null)
5. Create PERSON_WORKITEM_ROLE: Assign John Doe as PI on ALS Research Initiative

#### Adding a Project
6. Create WORK_ITEM (PROJECT): "Biomarker Discovery" (parent_work_item_id → ALS Research Initiative)
7. Create PERSON: "Jane Smith"
8. Create PERSON_ROLE: "Project Manager"
9. Create PERSON_WORKITEM_ROLE: Assign Jane Smith as PM on Biomarker Discovery

#### Adding a Study
10. Create WORK_ITEM (STUDY): "Voice Analysis Pilot" (parent_work_item_id → Biomarker Discovery)
11. Create PERSON: "Bob Johnson"
12. Create PERSON_ROLE: "Data Scientist"
13. Create PERSON_WORKITEM_ROLE: Assign Bob Johnson as Data Scientist on Voice Analysis Pilot

### 7. Query Examples

Once implemented in CoreModels, you can query:

- **All persons in an organization:**
  - Start from Organization → Follow "representing" relation → Get all Persons

- **All projects in a program:**
  - Start from WorkItem (type=PROGRAM) → Follow reverse "parent hierarchy" → Get WorkItems where type=PROJECT

- **All assignments for a person:**
  - Start from Person → Follow reverse "assigned to" → Get all PersonWorkItemRole assignments

- **Team members on a work item:**
  - Start from WorkItem → Follow reverse "works on" → Get PersonWorkItemRole → Follow "assigned to" → Get Persons

- **Active assignments:**
  - Filter PersonWorkItemRole where is_active = true

### 8. Validation & Constraints

Add these validations in CoreModels:

1. **Primary Keys:** All ID fields should be unique
2. **Foreign Keys:** Reference integrity checks
3. **Enum Values:** work_item_type limited to PROGRAM|PROJECT|STUDY
4. **Email Format:** Validate email pattern for Person.email
5. **Date Logic:** end_date should be >= start_date
6. **Hierarchy Logic:** Validate parent_work_item_id points to correct type
7. **Required Fields:** Enforce required=true constraints

### 9. JSON Schema Files Reference

All 5 schemas are available in:
- `docs/sage-schemas/Organization.schema.json`
- `docs/sage-schemas/Person.schema.json`
- `docs/sage-schemas/PersonRole.schema.json`
- `docs/sage-schemas/WorkItem.schema.json`
- `docs/sage-schemas/PersonWorkItemRole.schema.json`

---

## Implementation Checklist

- [ ] Create "Schema - Sage" space in CoreModels
- [ ] Import or create 5 Type nodes
- [ ] Add all Elements to each Type with correct data types
- [ ] Mark required fields
- [ ] Create Taxonomy for work_item_type
- [ ] Create 7 Relation groups between Types
- [ ] Add sample data to test relationships
- [ ] Validate hierarchy constraints
- [ ] Document standard workflows
- [ ] Set up access controls (if needed)

---

**Last Updated:** February 25, 2026  
**CoreModels Project:** 63c223a44f5e43acb8ae92763f08fa86  
**Target Space:** Schema - Sage
