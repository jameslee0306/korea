// usage: node tools/snap.js outdir t1 t2 ...  — 지정한 시각의 프레임을 PNG로 저장
const {chromium}=require('playwright');const path=require('path'),fs=require('fs');
(async()=>{const[out,...ts]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
  p.on('pageerror',e=>console.error('PAGEERR',e.message));p.on('console',m=>console.log('console',m.text()));
  await p.goto('file://'+path.resolve(__dirname,'../index.html')+'?render=1');await p.evaluate('window.ready');
  for(const t of ts){const d=await p.evaluate(t=>{render(+t);return document.getElementById('c').toDataURL('image/jpeg',.85).slice(23)},t);
    fs.writeFileSync(path.join(out,`f_${t}.jpg`),Buffer.from(d,'base64'))}
  await b.close()})();
