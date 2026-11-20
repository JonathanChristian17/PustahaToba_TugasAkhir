// Periksa penyajian terhadap keluaran tersimpan; tidak menjalankan model.
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath} from 'node:url'
import {adaptApiPayloadToUiItem, displayReading, unresolvedReadingUnits, buildTransliterationJson, buildTransliterationTxt} from '../../04_WEB_APP_BATAK_TOBA/src/utils/transliterationAdapter.js'

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..')
const folder=path.join(root,'05_HASIL/TAHAP_15_AUDIT_TRANSLITERASI_051/per_citra')
const files=fs.readdirSync(folder).filter(f=>f.endsWith('.json'))
assert.equal(files.length,131)
let unresolved=0
for (const file of files) {
  const tr=JSON.parse(fs.readFileSync(path.join(folder,file),'utf8'))
  const before=JSON.stringify(tr)
  const item=adaptApiPayloadToUiItem({source_name:file,transliteration:tr,detections:[]})
  assert.equal(displayReading(item.rawLatinText),tr.presentation.automatic_text)
  assert.equal(displayReading(item.literalText),tr.presentation.literal_text)
  assert.equal(displayReading(item.wordSpacing.suggested_text),tr.presentation.spacing_suggestion)
  assert(!buildTransliterationTxt(item).includes('[?]'))
  assert.deepEqual(JSON.parse(buildTransliterationJson(item)).hasil_modul,tr)
  assert.equal(JSON.stringify(tr),before)
  for (const group of item.overlappingCandidates) {
    if (group.selectedInstanceId==null) assert.equal(group.chosen,null)
    else assert.equal(group.chosen.instanceId,group.selectedInstanceId)
  }
  if (unresolvedReadingUnits(item).length) {
    unresolved++
    assert(buildTransliterationTxt(item).includes('Belum terbaca:'))
    assert(unresolvedReadingUnits(item).every(u=>u.reasons.length>0))
  }
}
assert.equal(unresolved,4)
assert.equal(displayReading('pi[?]nianggi'),'pi⟦belum terbaca⟧nianggi')
console.log(JSON.stringify({images:files.length,unresolved_images:unresolved,presentation_preserves_uncertainty:true,diagnostic_json_unchanged:true},null,2))
