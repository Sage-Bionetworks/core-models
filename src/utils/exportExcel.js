import ExcelJS from 'exceljs'
import { schemaUri } from './uri.js'
import { fetchDataModel, normName, defKey } from './dataModelSource.js'

const PROD_BASE = 'https://repo-prod.prod.sagebase.org/repo/v1/schema/type/registered/'

const N_MANIFEST_ROWS = 1000   // styled/validated data rows below the header

// Colours — match the R template / FileAnnotationTemplate.xlsx
const FILL_REQUIRED     = 'FFB5E3E8'   // teal   — required columns
const FILL_NONREQ_HDR   = 'FFE0E0E0'   // gray   — non-required column headers
const BORDER_GRID       = 'FFE2E3E3'   // medium grid border on the Manifest
const FILL_DD_HDR       = 'FF375623'   // dark green — DataDictionary header
const FILL_DD_BAND      = 'FFEBF3E8'   // light green — DataDictionary banding
const FILL_CF_RED       = 'FFFFC7CE'   // red — conditional-format flag

const FONT = { name: 'Arial', size: 10 }

// ─── Column index → Excel letter (1 → A, 27 → AA, …) ────────
function colLetter(n) {
  let s = ''
  while (n > 0) { n--; s = String.fromCharCode(65 + (n % 26)) + s; n = Math.floor(n / 26) }
  return s
}

// ─── Download a workbook buffer ──────────────────────────────
async function downloadWorkbook(wb, filename) {
  const buffer = await wb.xlsx.writeBuffer()
  const blob = new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// ─── Extract enumerated values wherever they live ────────────
// JSON schema properties express allowed values in several shapes:
//   • prop.enum                    — a plain single-value enum
//   • prop.type==='array' + items.enum — a LIST of allowed values (multi-value)
//   • prop.anyOf[].enum            — a hybrid (e.g. a free number/string OR an enum)
// Returns { values, multi, strict } or null.
//   multi  = the field holds a list (array) of values
//   strict = the enum is the only allowed form (a closed set); when false the field
//            also permits free / comma-separated entry, so validation must not block.
function extractEnum(prop) {
  if (!prop) return null

  const types = Array.isArray(prop.type) ? prop.type : (prop.type ? [prop.type] : [])
  const isArray = types.includes('array')

  if (Array.isArray(prop.enum) && prop.enum.length) {
    return { values: prop.enum, multi: false, strict: true }
  }
  if (isArray && prop.items && Array.isArray(prop.items.enum) && prop.items.enum.length) {
    return { values: prop.items.enum, multi: true, strict: false }
  }
  if (Array.isArray(prop.anyOf)) {
    const branch = prop.anyOf.find(b => Array.isArray(b.enum) && b.enum.length)
    if (branch) return { values: branch.enum, multi: false, strict: false }
  }
  return null
}

// ─── Flatten a schema's own top-level properties into attribute rows ──
// Mirrors the R extract_attrs step: name, description, type, valid values,
// required. Column/reference order follows the JSON schema's property order.
function extractAttributes(schema) {
  const props = schema.properties || {}
  const required = new Set(schema.required || [])

  return Object.keys(props).map(name => {
    const prop = props[name]
    const types = Array.isArray(prop.type) ? prop.type : (prop.type ? [prop.type] : [])
    const enumInfo = extractEnum(prop)
    return {
      attribute:   name,
      description: prop.description || '',
      type:        Array.isArray(prop.type) ? prop.type.join(' | ') : (prop.type || ''),
      isArray:     types.includes('array'),
      validValues: enumInfo ? enumInfo.values.map(v => String(v)) : null,
      enumInfo,
      prop,
      required:    required.has(name),
    }
  })
}

// ─── Reorder attributes to the data model's DependsOn order ──
// Attributes named in DependsOn come first, in that order; anything the model
// didn't list is appended in schema order. No source model → unchanged.
function reorderByDependsOn(attrs, schemaName, orderByTemplate) {
  const ordered = orderByTemplate?.get(normName(schemaName))
  if (!ordered) return attrs

  const byName = new Map(attrs.map(a => [a.attribute, a]))
  const matched = ordered.filter(n => byName.has(n))
  const leftover = attrs.map(a => a.attribute).filter(n => !matched.includes(n))
  return [...matched, ...leftover].map(n => byName.get(n))
}

// ─── Build the Manifest (+ hidden ValidValues) sheets ────────
function buildManifestSheets(wb, attrs, schemaName) {
  const wsManifest = wb.addWorksheet('Manifest')
  const wsLists    = wb.addWorksheet('ValidValues')   // hidden lookup, populated below

  const n = attrs.length
  const gridBorder = () => ({
    top:    { style: 'medium', color: { argb: BORDER_GRID } },
    bottom: { style: 'medium', color: { argb: BORDER_GRID } },
    left:   { style: 'medium', color: { argb: BORDER_GRID } },
    right:  { style: 'medium', color: { argb: BORDER_GRID } },
  })

  // Base grid: border (and Arial font) on every cell of the table; required
  // columns additionally get the teal fill down the whole column.
  for (let row = 1; row <= N_MANIFEST_ROWS; row++) {
    for (let c = 1; c <= n; c++) {
      const cell = wsManifest.getCell(row, c)
      cell.border = gridBorder()
      cell.font = { ...FONT }
      if (attrs[c - 1].required) {
        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: FILL_REQUIRED } }
      }
    }
  }

  attrs.forEach((a, i) => {
    const colIdx = i + 1
    const ltr = colLetter(colIdx)

    // ── Header cell ──
    const hCell = wsManifest.getCell(1, colIdx)
    hCell.value = a.attribute
    hCell.font = { ...FONT, bold: true }
    hCell.alignment = { vertical: 'middle', horizontal: 'center' }
    hCell.border = gridBorder()
    hCell.fill = {
      type: 'pattern', pattern: 'solid',
      fgColor: { argb: a.required ? FILL_REQUIRED : FILL_NONREQ_HDR },
    }

    // ── Header comment carrying the property description ──
    if (a.description) {
      let note = a.description
      if (a.isArray && a.validValues) {
        note += '\n\nMultiple values allowed: type your selections separated by "; " ' +
                '(e.g. "Human; Mouse"). Excel will show a warning since it isn\'t a single ' +
                'listed value, but the entry is accepted.'
      }
      hCell.note = note
    }

    // ── Dropdown / validation ──
    const range = `${ltr}2:${ltr}${N_MANIFEST_ROWS}`
    if (a.enumInfo) {
      // Back the dropdown with a column on the hidden ValidValues sheet (values
      // start at row 1, matching the R template).
      a.validValues.forEach((val, j) => { wsLists.getCell(j + 1, colIdx).value = val })

      // Multi-value (array) and hybrid (anyOf) fields must allow free /
      // separated entry, so validation is non-blocking. A closed single-value
      // enum keeps a (still non-blocking) warning to nudge toward the list.
      const relaxed = a.enumInfo.multi || !a.enumInfo.strict
      wsManifest.dataValidations.add(range, {
        type: 'list',
        allowBlank: true,
        showDropDown: false,   // false = SHOW the dropdown arrow (exceljs/OOXML quirk)
        showErrorMessage: !relaxed,
        errorStyle: 'warning',
        errorTitle: 'Value not in standard list',
        error: "This entry isn't one of the standard values for this field. Keep it anyway?",
        formulae: [`ValidValues!$${ltr}$1:$${ltr}$${a.validValues.length}`],
      })
    }
    // Non-enum columns carry no validation, matching the source template.
    // Free-text / multi-value guidance lives in the header comment instead.
  })

  // ── Pre-fill Component column (row 2) with the schema name if present ──
  const compIdx = attrs.findIndex(a => a.attribute.toLowerCase() === 'component')
  if (compIdx >= 0) wsManifest.getCell(2, compIdx + 1).value = schemaName

  // ── Conditional flag: species empty while resourceType is experimentalData ──
  const rtIdx = attrs.findIndex(a => a.attribute === 'resourceType')
  const spIdx = attrs.findIndex(a => a.attribute === 'species')
  if (rtIdx >= 0 && spIdx >= 0) {
    const rt = colLetter(rtIdx + 1)
    const sp = colLetter(spIdx + 1)
    wsManifest.addConditionalFormatting({
      ref: `${sp}2:${sp}${N_MANIFEST_ROWS}`,
      rules: [{
        style: { fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: FILL_CF_RED } } },
    })
  }

  wsLists.state = 'hidden'
}

// ─── Build the DataDictionary sheet ──────────────────────────
function buildDataDictionary(wb, attrs, definitions) {
  const ws = wb.addWorksheet('DataDictionary')
  const HEADERS = ['Property', 'Description', 'Value', 'Definition']

  // One row per (attribute, valid value); attributes without an enum get a
  // single blank-value row. Mirrors the R separate_rows + left_join.
  const rows = []
  for (const a of attrs) {
    const values = a.validValues && a.validValues.length ? a.validValues : ['']
    for (const v of values) {
      rows.push({
        Property:    a.attribute,
        Description: a.description,
        Value:       v,
        Definition:  v ? (definitions?.get(defKey(a.attribute, v)) || '') : '',
      })
    }
  }

  ws.addRow(HEADERS)
  rows.forEach(r => ws.addRow(HEADERS.map(h => r[h])))

  const nRows = rows.length + 1

  // Base: thin border + Arial across the whole table.
  const thin = { style: 'thin' }
  const thinAll = { top: thin, bottom: thin, left: thin, right: thin }
  for (let row = 1; row <= nRows; row++) {
    for (let c = 1; c <= HEADERS.length; c++) {
      const cell = ws.getCell(row, c)
      cell.border = thinAll
      cell.font = { ...FONT }
    }
  }

  // Header: white bold on dark green, left aligned.
  ws.getRow(1).eachCell(cell => {
    cell.font = { ...FONT, bold: true, color: { argb: 'FFFFFFFF' } }
    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: FILL_DD_HDR } }
    cell.alignment = { horizontal: 'left', vertical: 'top', wrapText: true }
  })

  // Body: wrap text, top aligned; banded shading per Property group (odd groups).
  let groupIdx = 0
  let prevProp = null
  for (let i = 0; i < rows.length; i++) {
    const rowNum = i + 2
    if (rows[i].Property !== prevProp) { groupIdx++; prevProp = rows[i].Property }
    const shade = groupIdx % 2 === 1
    ws.getRow(rowNum).eachCell(cell => {
      cell.alignment = { horizontal: 'left', vertical: 'top', wrapText: true }
      if (shade) cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: FILL_DD_BAND } }
    })
  }

  ws.getColumn(1).width = 28.7
  ws.getColumn(2).width = 40.7
  ws.getColumn(3).width = 32.7
  ws.getColumn(4).width = 60.7
  ws.views = [{ state: 'frozen', ySplit: 1 }]
  ws.autoFilter = { from: { row: 1, column: 1 }, to: { row: 1, column: HEADERS.length } }
}

// ─── Export a SINGLE schema from the detail panel ────────────
export async function exportSchemaToExcel(orgName, schemaName) {
  const uri = `${orgName}-${schemaName}`
  const response = await fetch(PROD_BASE + uri)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  const schema = await response.json()

  // Per-DCC source model (definitions + DependsOn order); null → graceful fallback.
  const model = await fetchDataModel(orgName)

  let attrs = extractAttributes(schema)
  attrs = reorderByDependsOn(attrs, schemaName, model?.orderByTemplate)

  const wb = new ExcelJS.Workbook()
  wb.creator = 'core-models'

  buildManifestSheets(wb, attrs, schemaName)
  buildDataDictionary(wb, attrs, model?.definitions)

  await downloadWorkbook(wb, `${schemaName}.xlsx`)
}

// ─── Export the FILTERED list from the toolbar ───────────────
export async function exportListToExcel(rows, stagingResults) {
  const KEYS = [
    'Org Name','Schema Name','URI','Status','Version','Created',
    'Staging','Org ID','Schema ID','Version ID','Created By','SHA256',
  ]

  const wb = new ExcelJS.Workbook()
  const ws = wb.addWorksheet('Schemas')
  ws.views = [{ state: 'frozen', xSplit: 0, ySplit: 1 }]

  const hdr = ws.addRow(KEYS)
  hdr.font = { bold: true }
  hdr.eachCell(cell => {
    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFE0E0E0' } }
  })

  rows.forEach(row => {
    const uri = `${row.organization_name}-${row.schema_name}`
    const sr  = stagingResults[uri]
    ws.addRow([
      row.organization_name || '',
      row.schema_name       || '',
      schemaUri(row),
      row.status            || '',
      row.semantic_version  || '',
      row.created_on ? new Date(row.created_on).toISOString() : '',
      sr === undefined ? '' : sr.ok ? 'Pass' : 'Fail',
      row.organization_id   || '',
      row.schema_id         || '',
      row.version_id        || '',
      row.created_by        || '',
      row.json_sha256_hex   || '',
    ])
  })

  KEYS.forEach((k, i) => {
    const col = ws.getColumn(i + 1)
    const vals = rows.map(r => {
      const cells = [
        r.organization_name, r.schema_name, schemaUri(r), r.status, r.semantic_version,
        r.created_on, '', r.organization_id, r.schema_id,
        r.version_id, r.created_by, r.json_sha256_hex,
      ]
      return String(cells[i] ?? '').length
    })
    col.width = Math.min(60, Math.max(k.length + 2, ...vals) + 2)
  })

  await downloadWorkbook(wb, 'schemas-export.xlsx')
}
