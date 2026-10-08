// usage: node tools/render.js out_dir [fps]  — 프레임을 렌더해 video.mp4(무음) + keys.json 생성
const {chromium}=require('playwright');const path=require('path'),fs=require('fs'),{spawn}=require('child_process');
(async()=>{const out=process.argv[2],fps=+(process.argv[3]||60);fs.mkdirSync(out,{recursive:true});
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
  p.on('pageerror',e=>console.error('PAGEERR',e.message));
  await p.goto('file://'+path.resolve(__dirname,'../index.html')+'?render=1');await p.evaluate('window.ready');
  fs.writeFileSync(path.join(out,'keys.json'),JSON.stringify(await p.evaluate(()=>({keys:KEYS,bells:BELLS}))));
  const ff=spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-',
    '-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',path.join(out,'video.mp4')],{stdio:['pipe','inherit','inherit']});
  const N=Math.round(30*fps);
  for(let i=0;i<N;i++){const d=await p.evaluate(t=>{render(t);return document.getElementById('c').toDataURL('image/jpeg',.97).slice(23)},i/fps);
    if(!ff.stdin.write(Buffer.from(d,'base64')))await new Promise(r=>ff.stdin.once('drain',r));
    if(i%120===0)console.log('frame',i,'/',N)}
  ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close()})();
