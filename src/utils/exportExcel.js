import ExcelJS from 'exceljs'
import { schemaUri } from './uri.js'

const PROD_BASE = 'https://repo-prod.prod.sagebase.org/repo/v1/schema/type/registered/'

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

// ─── Resolve $ref within the schema's $defs / definitions ────
function resolveRef(ref, schema) {
  if (!ref?.startsWith('#')) return null
  const parts = ref.replace(/^#\//, '').split('/')
  let node = schema
  for (const p of parts) node = node?.[p]
  return node || null
}

// ─── Flatten schema properties into rows ─────────────────────
function flattenProperties(schema, prefix = '', parentRequired = new Set()) {
  const rows = []
  const props = schema.properties || {}
  const required = new Set([...(schema.required || []), ...parentRequired])

  for (const [name, rawProp] of Object.entries(props)) {
    let prop = rawProp
    if (prop.$ref) {
      const resolved = resolveRef(prop.$ref, schema)
      prop = resolved ? { ...resolved, ...prop, $ref: undefined } : prop
    }
    const fullName = prefix ? `${prefix}.${name}` : name
    const type = Array.isArray(prop.type) ? prop.type.join(' | ') : (prop.type || '')
    // Surface enumerated values wherever they live so the reference sheet stays complete.
    const enumVals = extractEnum(prop)?.values || prop.examples || []

    rows.push({
      'Property':    fullName,
      'Type':        type || (prop.$ref ? '$ref' : ''),
      'Required':    required.has(name) ? 'Yes' : '',
      'Description': prop.description || '',
      'Enum Values': enumVals.map(v => String(v)).join(', '),
      'Const':       prop.const !== undefined ? String(prop.const) : '',
      'Default':     prop.default !== undefined ? String(prop.default) : '',
      'Format':      prop.format || '',
      'Pattern':     prop.pattern || '',
      'Min Length':  prop.minLength !== undefined ? prop.minLength : '',
      'Max Length':  prop.maxLength !== undefined ? prop.maxLength : '',
      'Minimum':     prop.minimum !== undefined ? prop.minimum : '',
      'Maximum':     prop.maximum !== undefined ? prop.maximum : '',
    })

    if (type === 'object' && prop.properties) rows.push(...flattenProperties(prop, fullName))
    if (type === 'array' && prop.items?.properties) rows.push(...flattenProperties(prop.items, `${fullName}[]`))
  }

  for (const combiner of ['allOf', 'anyOf', 'oneOf']) {
    if (schema[combiner]) {
      rows.push({
        'Property': `(${combiner})`, 'Type': combiner, 'Required': '',
        'Description': `${schema[combiner].length} subschema(s)`,
        'Enum Values': '', 'Const': '', 'Default': '', 'Format': '',
        'Pattern': '', 'Min Length': '', 'Max Length': '', 'Minimum': '', 'Maximum': '',
      })
    }
  }
  return rows
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
  if (Array.isArray(prop.enum) && prop.enum.length) {
    return { values: prop.enum, multi: false, strict: true }
  }
  if (prop.type === 'array' && prop.items && Array.isArray(prop.items.enum) && prop.items.enum.length) {
    return { values: prop.items.enum, multi: true, strict: false }
  }
  if (Array.isArray(prop.anyOf)) {
    const branch = prop.anyOf.find(b => Array.isArray(b.enum) && b.enum.length)
    if (branch) return { values: branch.enum, multi: false, strict: false }
  }
  return null
}

// ─── Build the Template + Lists sheets ───────────────────────
function buildTemplateSheets(wb, schema, schemaName) {
  const props   = schema.properties || {}
  const required = new Set(schema.required || [])
  // Column order follows the JSON schema's property order exactly (insertion order).
  const names   = Object.keys(props)

  // Fill styles — match the example file's colours
  const FILL_BLUE_HDR  = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFEAF7F9' } }
  const FILL_BLUE_DATA = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFD6EAF8' } }
  const FILL_GRAY_HDR  = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFE0E0E0' } }
  const BORDER_THIN    = { style: 'thin', color: { argb: 'FFBDD7EE' } }

  // Template sheet (first visible tab)
  const wsTmpl = wb.addWorksheet('Template')

  // Lists sheet added AFTER Template so tab order is: Template … Lists(hidden)
  // We'll populate it below then hide it at the end
  const wsLists = wb.addWorksheet('Lists')
  wsTmpl.views = [{ state: 'frozen', xSplit: 0, ySplit: 1 }]

  names.forEach((name, i) => {
    const colIdx = i + 1
    const ltr    = colLetter(colIdx)
    const prop     = props[name]
    const isReq    = required.has(name)
    const enumInfo = extractEnum(prop)        // {values, multi, strict} | null
    const isList   = prop.type === 'array'    // a list field (with or without an enum)

    // Column width
    wsTmpl.getColumn(colIdx).width = Math.max(name.length + 2, 14)

    // ── Header cell ──
    const hCell = wsTmpl.getCell(1, colIdx)
    hCell.value = name
    hCell.font  = { bold: true, size: 11 }
    hCell.fill  = isReq ? FILL_BLUE_HDR : FILL_GRAY_HDR
    hCell.alignment = { vertical: 'middle', horizontal: 'center', wrapText: false }
    hCell.border = {
      bottom: { style: 'medium', color: { argb: isReq ? 'FF5BA3C9' : 'FFB0B0B0' } },
    }

    // ── Blue column fill for data rows (rows 2–500) ──
    if (isReq) {
      for (let row = 2; row <= 500; row++) {
        const cell = wsTmpl.getCell(row, colIdx)
        cell.fill = FILL_BLUE_DATA
        cell.border = { left: BORDER_THIN, right: BORDER_THIN }
      }
    }

    // ── Dropdown for enumerated values (direct enum, array items.enum, or anyOf branch) ──
    if (enumInfo) {
      // Back the dropdown with a column on the hidden Lists sheet.
      wsLists.getCell(1, colIdx).value = name
      enumInfo.values.forEach((val, j) => { wsLists.getCell(j + 2, colIdx).value = val })

      // Multi-value (array) and hybrid (anyOf) fields must allow free / comma-separated
      // entry, so their validation is non-blocking. A closed single-value enum keeps a
      // (still non-blocking) warning to nudge toward the list.
      const relaxed = enumInfo.multi || !enumInfo.strict
      wsTmpl.dataValidations.add(`${ltr}2:${ltr}500`, {
        type: 'list',
        allowBlank: true,
        showDropDown: false,   // false = SHOW the dropdown arrow (exceljs/OOXML quirk)
        showErrorMessage: !relaxed,
        errorStyle: 'warning',
        errorTitle: 'Value not in list',
        error: 'Choose a value from the dropdown list.',
        showInputMessage: true,
        promptTitle: enumInfo.multi ? 'Multiple values allowed' : 'Pick from the list',
        prompt: enumInfo.multi
          ? 'Pick a value from the dropdown, or enter multiple values separated by commas.'
          : 'Pick a value from the dropdown.',
        formulae: [`Lists!$${ltr}$2:$${ltr}$${enumInfo.values.length + 1}`],
      })
    } else if (isList) {
      // Array of free-text values (no enum) — permit multiple comma-separated values.
      // A custom "always true" rule never blocks; it just carries the input message.
      wsTmpl.dataValidations.add(`${ltr}2:${ltr}500`, {
        type: 'custom',
        allowBlank: true,
        formulae: ['TRUE'],
        showInputMessage: true,
        promptTitle: 'Multiple values allowed',
        prompt: 'Enter one or more values separated by commas.',
      })
    } else if (prop.type === 'integer' || prop.type === 'number') {
      // Numeric validation
      const hasMin = prop.minimum !== undefined
      const hasMax = prop.maximum !== undefined
      const operator = hasMin && hasMax ? 'between'
                     : hasMin ? 'greaterThanOrEqual'
                     : hasMax ? 'lessThanOrEqual'
                     : null
      if (operator) {
        const formulae = hasMin && hasMax
          ? [prop.minimum, prop.maximum]
          : hasMin ? [prop.minimum] : [prop.maximum]
        wsTmpl.dataValidations.add(`${ltr}2:${ltr}500`, {
          type: prop.type === 'integer' ? 'whole' : 'decimal',
          allowBlank: true,
          showErrorMessage: true,
          errorStyle: 'warning',
          errorTitle: 'Invalid value',
          error: `Must be a ${prop.type}${hasMin ? ` ≥ ${prop.minimum}` : ''}${hasMax ? ` ≤ ${prop.maximum}` : ''}.`,
          operator,
          formulae,
        })
      }
    } else if (prop.maxLength !== undefined || prop.minLength !== undefined) {
      // Text length validation
      const hasMin = prop.minLength !== undefined
      const hasMax = prop.maxLength !== undefined
      const operator = hasMin && hasMax ? 'between'
                     : hasMin ? 'greaterThanOrEqual'
                     : 'lessThanOrEqual'
      wsTmpl.dataValidations.add(`${ltr}2:${ltr}500`, {
        type: 'textLength',
        allowBlank: true,
        showErrorMessage: true,
        errorStyle: 'warning',
        errorTitle: 'Text too long',
        error: `Length must be${hasMin ? ` ≥ ${prop.minLength}` : ''}${hasMax ? ` ≤ ${prop.maxLength}` : ''}.`,
        operator,
        formulae: hasMin && hasMax ? [prop.minLength, prop.maxLength]
                : hasMin ? [prop.minLength] : [prop.maxLength],
      })
    }
  })

  // Pre-fill Component column (row 2) with schema name if applicable
  const compIdx = names.findIndex(n => n.toLowerCase() === 'component')
  if (compIdx >= 0) {
    wsTmpl.getCell(2, compIdx + 1).value = schemaName
  }

  // Row 1 height
  wsTmpl.getRow(1).height = 22

  // Hide the Lists lookup sheet — must be done after all cells are populated
  wsLists.state = 'hidden'
}

// ─── Export a SINGLE schema from the detail panel ────────────
export async function exportSchemaToExcel(orgName, schemaName) {
  const uri = `${orgName}-${schemaName}`
  const response = await fetch(PROD_BASE + uri)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  const schema = await response.json()

  const wb = new ExcelJS.Workbook()

  // ── Sheet 1: Template (+ hidden Lists) ──
  buildTemplateSheets(wb, schema, schemaName)

  const PROP_KEYS = [
    'Property','Type','Required','Description','Enum Values',
    'Const','Default','Format','Pattern','Min Length','Max Length','Minimum','Maximum',
  ]

  // ── Sheet 2: Properties ──
  const wsProps = wb.addWorksheet('Properties')
  wsProps.views = [{ state: 'frozen', xSplit: 0, ySplit: 1 }]
  const propRows = flattenProperties(schema)

  // Header row
  const hdr = wsProps.addRow(PROP_KEYS)
  hdr.font = { bold: true }
  hdr.eachCell(cell => {
    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFE0E0E0' } }
  })

  propRows.forEach(r => wsProps.addRow(PROP_KEYS.map(k => r[k] ?? '')))

  PROP_KEYS.forEach((k, i) => {
    const maxLen = Math.max(k.length, ...propRows.map(r => String(r[k] ?? '').length))
    wsProps.getColumn(i + 1).width = Math.min(60, maxLen + 2)
  })

  // Sheets are intentionally limited to Template (+ hidden Lists) and Properties.
  // The former Enums and Metadata reference sheets were removed.

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
