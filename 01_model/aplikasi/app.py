"""Lembar pemeriksaan citra, segmentasi dan klasifikasi aksara Batak Toba."""
import hashlib
import importlib
import logging
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from PIL import Image
from backend import Predictor, decode_upload, displayed, export_files, save_result, table_rows, open_result_folder, DISPLAY_THRESHOLD
import visual
importlib.reload(visual)
from visual import render_pair

MODES = ("Mask + Bbox", "Mask", "Bbox")
if st.session_state.get('view_mode') not in MODES:
    st.session_state.pop('view_mode', None)

BASE=Path(__file__).resolve().parent
st.set_page_config(page_title='Segmentasi dan Klasifikasi Aksara Batak Toba',layout='wide',initial_sidebar_state='collapsed')
st.markdown('<style>'+(BASE/'assets/style.css').read_text(encoding='utf-8')+'</style>',unsafe_allow_html=True)
components.html("""<script>
(function() {
  var doc = window.parent.document;
  var win = window.parent;
  if (!doc || win._stImgLightboxInit) return;
  win._stImgLightboxInit = true;

  var modal = doc.createElement('div');
  modal.id = 'st-img-lightbox-modal';
  modal.style.cssText = 'display:none;position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(11,15,25,0.92);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);z-index:99999999;align-items:center;justify-content:center;cursor:zoom-out;box-sizing:border-box;padding:20px;';

  var closeBtn = doc.createElement('div');
  closeBtn.style.cssText = 'position:fixed;top:20px;right:24px;color:#ffffff;background:rgba(255,255,255,0.18);padding:8px 16px;border-radius:4px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:13px;font-weight:600;cursor:pointer;border:1px solid rgba(255,255,255,0.35);user-select:none;z-index:100000000;box-shadow:0 2px 10px rgba(0,0,0,0.4);';
  closeBtn.textContent = '✕ Tutup (ESC)';

  var modalImg = doc.createElement('img');
  modalImg.style.cssText = 'max-width:96vw;max-height:94vh;object-fit:contain;border-radius:4px;box-shadow:0 12px 48px rgba(0,0,0,0.7);cursor:default;';
  modalImg.onclick = function(e) { e.stopPropagation(); };

  modal.appendChild(closeBtn);
  modal.appendChild(modalImg);
  doc.body.appendChild(modal);

  function closeModal() {
    modal.style.display = 'none';
  }

  modal.onclick = closeModal;
  closeBtn.onclick = closeModal;
  doc.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeModal();
  });

  doc.addEventListener('click', function(e) {
    var img = e.target.closest('[data-testid="stImage"] img');
    if (img && img.src) {
      modalImg.src = img.src;
      modal.style.display = 'flex';
    }
  });
})();
</script>""", height=0, width=0)

@st.cache_resource(show_spinner=False)
def load_predictor():return Predictor()

st.markdown('<h1>Segmentasi dan Klasifikasi Aksara Batak Toba</h1>',unsafe_allow_html=True)
st.markdown('<p class="app-subtitle">Implementasi Mask R-CNN untuk Karakter Tulisan Tangan · Aksara Batak Toba</p>',unsafe_allow_html=True)
model_line=st.empty()
choose,process,folder,space,progress_col=st.columns([1.15,1.2,1.4,3.3,1.2],vertical_alignment='center',gap='small')
with choose:uploaded=st.file_uploader('1 Pilih citra',type=['png','jpg','jpeg','webp'],label_visibility='collapsed')
payload=uploaded.getvalue() if uploaded is not None else None
inputkey=(hashlib.sha256(payload).hexdigest(),uploaded.name) if payload is not None else None
if inputkey!=st.session_state.get('input_key'):
    for key in ['result','rgb','saved_path','saved_mode','failure']:st.session_state.pop(key,None)
    st.session_state['input_key']=inputkey
with process:detect=st.button('2 Proses citra',disabled=payload is None,width='stretch',key='process')
with folder:open_folder=st.button('Buka folder hasil',disabled=not st.session_state.get('saved_path'),width='stretch',key='open_folder')
with progress_col:progress=st.progress(100 if 'result' in st.session_state else 0)
st.caption(uploaded.name if uploaded else 'Belum ada citra dipilih.')

rgb=None
if payload is not None:
    try:rgb=decode_upload(payload)
    except ValueError as error:st.error(str(error));st.stop()
if detect:
    progress.progress(15)
    try:
        model=load_predictor();progress.progress(40)
        st.session_state['loaded_model_identity']=dict(model.model_identity)
        result=model.predict(rgb,uploaded.name,hashlib.sha256(payload).hexdigest())
        st.session_state.update(rgb=rgb,result=result)
        for key in ['failure','saved_path','saved_mode']:st.session_state.pop(key,None)
        progress.progress(85)
    except Exception as error:
        logging.exception('Inferensi web gagal')
        for k in ['result','rgb','saved_path','saved_mode']:st.session_state.pop(k,None)
        st.session_state['failure']=str(error);progress.progress(0)
if open_folder:
    try:open_result_folder(st.session_state['saved_path'])
    except (OSError,RuntimeError,ValueError) as error:st.error('Folder hasil tidak dapat dibuka: '+str(error))

identity=st.session_state.get('loaded_model_identity')
threshold=f'{DISPLAY_THRESHOLD:.2f}'.replace('.',',')
identity_text=(f'ResNet-{identity["backbone_depth"]}-FPN · Epoch {identity["epoch"]}'
               if identity else 'Model belum dimuat')
model_line.markdown(f'<p class="model-line">{identity_text} · Ambang confidence ≥ {threshold}</p>',unsafe_allow_html=True)

lefthead,righthead=st.columns(2,gap='medium',vertical_alignment='bottom')
with lefthead:st.markdown('<h2 class="desktop-panel-label">CITRA MASUKAN</h2>',unsafe_allow_html=True)
with righthead:
    label,control=st.columns([2,1],vertical_alignment='bottom')
    with label:st.markdown('<h2 class="desktop-panel-label">MASK DAN LABEL PREDIKSI</h2>',unsafe_allow_html=True)
    with control:mode=st.selectbox('Tampilan',MODES,label_visibility='collapsed',key='view_mode')
result=st.session_state.get('result');items=displayed(result) if result else []
left,right=st.columns(2,gap='medium')
with left:
    st.markdown('<h2 class="mobile-panel-label">CITRA MASUKAN</h2>',unsafe_allow_html=True)
    original_view=st.empty()
with right:
    st.markdown('<h2 class="mobile-panel-label">MASK DAN LABEL PREDIKSI</h2>',unsafe_allow_html=True)
    overlay_view=st.empty()
st.markdown(f'<p class="count-line">{len(items)} instansi lolos threshold {threshold} · {len({x["class_label"] for x in items})} kelas</p>',unsafe_allow_html=True)
rows=table_rows(result) if result else []
frame=pd.DataFrame(rows,columns=['No.','Kelas prediksi','Confidence (%)','Bounding box [x1, y1, x2, y2]'])
table_key='instances_'+hashlib.sha256(repr((inputkey,result.get('created_utc') if result else None)).encode()).hexdigest()[:16]
event=st.dataframe(frame,hide_index=True,width='stretch',height=230,key=table_key,
             on_select='rerun',selection_mode='single-row',
             column_config={'No.':st.column_config.NumberColumn(width='small',format='%d'),
                            'Kelas prediksi':st.column_config.TextColumn(width='medium'),
                            'Confidence (%)':st.column_config.NumberColumn(width='small',format='%.1f%%'),
                            'Bounding box [x1, y1, x2, y2]':st.column_config.TextColumn(width='large')})
selected_rows=event.selection.rows
focus=int(frame.iloc[selected_rows[0]]['No.']) if selected_rows and 0<=selected_rows[0]<len(frame) else None
if rgb is None:original=overlay=Image.new('RGB',(1000,500),'white')
else:original,overlay,_=render_pair(rgb,items,mode,focus=focus)
original_view.image(original,width='stretch');overlay_view.image(overlay,width='stretch')
if st.session_state.get('failure'):st.error('Proses citra gagal: '+st.session_state['failure'])
elif result:
    try:
        if 'saved_path' not in st.session_state or st.session_state.get('saved_mode')!=mode:
            files=export_files(rgb,result,mode=mode);saved=save_result(files)
            st.session_state.update(saved_path=str(saved),saved_mode=mode)
            st.rerun()
        progress.progress(100)
        if not items:st.info('Tidak ada prediksi yang memenuhi ambang 0,50.')
        st.caption(f'Selesai. Inference {result["inference_seconds_excluding_load_and_resize"]:.2f} detik. Hasil disimpan otomatis.')
    except OSError as error:st.error('Prediksi tersedia, tetapi penyimpanan hasil gagal: '+str(error))
else:st.caption('Pilih citra lalu tekan Proses citra.')
