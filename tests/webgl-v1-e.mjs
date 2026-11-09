import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { chromium } from 'playwright';
import { PNG } from 'pngjs';

const folder=join(process.cwd(),'test-results','v1-e');
await mkdir(folder,{recursive:true});
const report={name:'StarCraft Diorama v1.4 classic RTS visual check',checks:[],errors:[],conclusion:'INCOMPLETE'};
const server=createServer(async (req,res)=>{
  if(new URL(req.url,'http://localhost').pathname!=='/3d.html'){res.writeHead(404);res.end();return;}
  try {
    const html=await readFile(join(process.cwd(),'3d.html'));
    res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});res.end(html);
  } catch(e){res.writeHead(500);res.end(String(e));}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const base='http://127.0.0.1:'+server.address().port+'/3d.html';
let browser;
const phases=[0,6.2,7.7,8,14.8,16.7,18,19.8,23,29,29.5,31.8,34.9];
async function check(phase,width,height,mobile=false){
  const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:1,isMobile:mobile,hasTouch:mobile});
  const page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  const label=(mobile?'mobile':'desktop')+'-'+width+'x'+height+'-'+String(phase).replace('.','_');
  try {
    await page.goto(base+'?phase='+phase+'&skin=0&assets=0',{waitUntil:'domcontentloaded',timeout:20000});
    await page.waitForFunction(()=>document.querySelector('#progress')?.style.width.endsWith('%'),null,{timeout:15000});
    await page.waitForTimeout(150);
    const state=await page.evaluate(()=>{
      const canvas=document.querySelector('#stage'),gl=canvas.getContext('webgl2');
      return {
        webgl2:!!gl,version:gl?.getParameter(gl.VERSION)||null,
        error:gl?.getError(),dimensions:gl?[gl.drawingBufferWidth,gl.drawingBufferHeight]:null, imageRendering:getComputedStyle(canvas).imageRendering,
        fallback:getComputedStyle(document.querySelector('#fallback')).display,
        progress:parseFloat(document.querySelector('#progress').style.width),
        pause:document.querySelector('#pause').getAttribute('aria-label')
      };
    });
    assert.ok(state.webgl2,label+': WebGL2 not available');
    assert.equal(state.error,0,label+': GPU error');
    // Real pixels are intentionally fewer than CSS pixels in the default classic RTS view.
    const renderScale=Math.min(.78,Math.max(.50,300/Math.min(width,height)));
    assert.deepEqual(state.dimensions,[Math.round(width*renderScale),Math.round(height*renderScale)],
      label+': pixel-mode framebuffer resolution');
    assert.equal(state.imageRendering,'pixelated',label+': not nearest-neighbor scaled');
    assert.equal(state.fallback,'none',label+': fallback shown');
    assert.equal(state.pause,'재생',label+': pause initial state');
    assert.ok(Math.abs(state.progress-phase/35*100)<.8,label+': incorrect phase progress');
    assert.deepEqual(errors,[],label+': uncaught JavaScript errors');
    if(phase===18 && width===1280 && !mobile) {
      const sizes=await page.evaluate(()=>{
        function bounds(make) {
          const m=new Mesh();make(m);
          const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
          for(let i=0;i<m.data.length;i+=9)for(let k=0;k<3;k++){
            const n=m.data[i+k];if(!Number.isFinite(n))throw Error('nonfinite vertex');
            lo[k]=Math.min(lo[k],n);hi[k]=Math.max(hi[k],n);
          }
          if(m.stack.length!==1)throw Error('matrix stack imbalance');
          return {width:hi[0]-lo[0],height:hi[1]-lo[1],depth:hi[2]-lo[2],vertices:m.data.length/9};
        }
        const models={
          marine:bounds(m=>marine(m,0,0,18,true,0,0)),
          scv:bounds(m=>scv(m,18)),
          tank:bounds(m=>tank(m,0,0,18,1,0)),
          factory:bounds(m=>factory(m)),
          machineShop:bounds(m=>machineShop(m)),
          armory:bounds(m=>armory(m)),
          supply:bounds(m=>supply(m)),
          bunker:bounds(m=>bunker(m))
        };
        const r=(a,az,b,bz)=>+(models[a][az]/models[b][bz]).toFixed(3);
        return {models,ratios:{
          scvMarineHeight:r('scv','height','marine','height'),
          scvMarineWidth:r('scv','width','marine','width'),
          tankMarineWidth:r('tank','width','marine','width'),
          shopFactory:r('machineShop','width','factory','width'),
          armoryFactory:r('armory','width','factory','width'),
          depotFactory:r('supply','width','factory','width'),
          bunkerFactory:r('bunker','width','factory','width')
        }};
      });
      const ranges={
        scvMarineHeight:[1.40,1.48],scvMarineWidth:[1.32,1.42],
        tankMarineWidth:[1.90,2.02],shopFactory:[.55,.70],
        armoryFactory:[.76,.91],depotFactory:[.62,.76],bunkerFactory:[.51,.66]
      };
      for(const [name,[low,high]]of Object.entries(ranges)){
        const ratio=sizes.ratios[name];
        assert.ok(ratio>=low&&ratio<=high,name+': '+ratio+' outside '+low+'–'+high);
      }
      report.proportions=sizes;
      const workerSites=await page.evaluate(()=>{
        const bbox=new Mesh();bunker(bbox);
        let right=-Infinity,front=-Infinity;
        for(let i=0;i<bbox.data.length;i+=9){right=Math.max(right,bbox.data[i]);front=Math.max(front,bbox.data[i+2]);}
        const poses=[0,6,12,18].map(t=>scvWorkPose(t));
        return {right,front,poses};
      });
      assert.ok(workerSites.poses.slice(0,3).every(p=>p.x>workerSites.right&&p.z>workerSites.front),
        'SCV work centers must remain outside bunker frame');
      const [a,b,c,loop]=workerSites.poses;
      assert.ok(Math.hypot(a.x-b.x,a.z-b.z)>.15&&Math.hypot(b.x-c.x,b.z-c.z)>.15,
        'SCV must visit three different sites');
      assert.equal(loop.x,a.x);assert.equal(loop.z,a.z);
      report.workerClearance=workerSites;
      const cannon=await page.evaluate(()=>{
        const m=new Mesh(); arcliteTwinBarrels(m);
        let zMin=Infinity,zMax=-Infinity,finite=true;
        for(let i=0;i<m.data.length;i+=9){
          zMin=Math.min(zMin,m.data[i+2]);zMax=Math.max(zMax,m.data[i+2]);
          if(!m.data.slice(i,i+9).every(Number.isFinite))finite=false;
        }
        return {zMin,zMax,depth:zMax-zMin,vertices:m.data.length/9,finite,stack:m.stack.length};
      });
      assert.ok(cannon.finite && cannon.stack===1 && cannon.vertices>500,'short cannon geometry invalid');
      assert.ok(cannon.depth>=.76 && cannon.depth<=.98,'cannon looks too long/short: '+cannon.depth);
      assert.ok(cannon.zMax<=1.16,'muzzle sticks out too far: '+cannon.zMax);
      assert.ok(cannon.zMax-.14<1.205,'muzzle exceeds the front of tank hull');
      report.arcliteTwinBarrels=cannon;
      // The wider tank body must still fit the actual open gate and fixed support posts.
      // Compare generated vertices, not a claimed official StarCraft dimension.
      const exit=await page.evaluate(()=>{
        const body=new Mesh();tank(body,0,0,18,1,0);
        const gate=new Mesh();factoryShutter(gate,8);
        const halfWidth=Math.max(...body.data.filter((_,i)=>i%9===0).map(Math.abs));
        const openInner=Math.min(...gate.data.filter((_,i)=>i%9===0).map(v=>Math.abs(v-.55)));
        const safety={
          movingGate:openInner-halfWidth,
          entrancePost:1.44-.29/2-halfWidth,
          sideSupport:1.43-.36/2-halfWidth
        };
        const rotated=new Mesh();tank(rotated,0,0,18,1,-.85);
        if(rotated.data.length!==body.data.length)throw Error('tank turn changes mesh size');
        let firstDifference=-1;
        for(let i=0;i<body.data.length;i++){
          if(Math.abs(body.data[i]-rotated.data[i])>1e-6){firstDifference=i;break;}
        }
        return {halfWidth,openInner,safety,firstDifferenceFraction:firstDifference/body.data.length};
      });
      assert.ok(exit.safety.movingGate>=.045,
        'Tank treads too close to opening shutter: '+exit.safety.movingGate);
      assert.ok(exit.safety.entrancePost>=.045,
        'Tank exceeds Factory door posts: '+exit.safety.entrancePost);
      assert.ok(exit.safety.sideSupport>=.015,
        'Tank too close to exterior door support: '+exit.safety.sideSupport);
      assert.ok(exit.firstDifferenceFraction>.74,
        'Hull or tracks rotate with turret; first changed mesh fraction '+exit.firstDifferenceFraction);
      report.factoryExitClearance=exit;
    }
    // A real screen-space check: the highest old Armory chimney must remain inside
    // both desktop and landscape-phone viewports (prior version cropped it).
    const topLandmarkY=await page.evaluate(()=>project3(-4.38,3.13,-3.71)[1]);
    assert.ok(topLandmarkY>=12,label+': Armory roof landmark clipped at '+topLandmarkY);
    const pngBuffer=await page.locator('#stage').screenshot({path:join(folder,label+'.png')});
    const png=PNG.sync.read(pngBuffer),colors=new Set();
    let lit=0,total=0;
    for(let y=0;y<png.height;y+=7)for(let x=0;x<png.width;x+=7){
      const i=(y*png.width+x)*4,r=png.data[i],g=png.data[i+1],b=png.data[i+2];
      colors.add(r+','+g+','+b);if(r+g+b>=65)lit++;total++;
    }
    assert.ok(colors.size>=30 && lit/total>.03,label+': black or blank canvas');
    report.checks.push({label,phase,version:state.version,colors:colors.size,litFraction:+(lit/total).toFixed(3),bytes:pngBuffer.length,armoryRoofY:+topLandmarkY.toFixed(1)});
    // Ship small targeted crops alongside full screenshots for human comparison
    // against user-supplied original StarCraft unit renders; no image assets copied.
    if(phase===18 && width===1280 && !mobile){
      const targets=await page.evaluate(()=>{
        const w=scvWorkPose(18);
        return {
          tank:project3(.55,1.0,1.08),
          marine:project3(-1.52,1.1,2.18),
          scv:project3(w.x,1.05,w.z)
        };
      });
      for(const [unit,[cx,cy]] of Object.entries(targets)){
        const cropWidth=230,cropHeight=190;
        const x=Math.max(0,Math.min(width-cropWidth,Math.round(cx-cropWidth/2)));
        const y=Math.max(0,Math.min(height-cropHeight,Math.round(cy-cropHeight/2)));
        await page.screenshot({path:join(folder,'closeup-'+unit+'-18.png'),
          clip:{x,y,width:cropWidth,height:cropHeight}});
      }
    }
    if(phase===18 && width===1280){
      // Accessible clean comparison: original full-resolution pipeline is still intact.
      const clean=await context.newPage();
      try{
        await clean.goto(base+'?phase=18&skin=0&assets=0&style=clean',{waitUntil:'domcontentloaded'});
        await clean.waitForFunction(()=>document.querySelector('#progress')?.style.width.endsWith('%'));
        const cleanState=await clean.evaluate(()=>{
          const c=document.querySelector('#stage'),g=c.getContext('webgl2');
          return {width:g.drawingBufferWidth,height:g.drawingBufferHeight,render:getComputedStyle(c).imageRendering,error:g.getError()};
        });
        assert.equal(cleanState.width,width,'clean mode must render at original resolution');
        assert.equal(cleanState.height,height,'clean mode must render at original resolution');
        assert.notEqual(cleanState.render,'pixelated','clean mode should not be pixel scaled');
        assert.equal(cleanState.error,0,'clean mode GPU error');
        await clean.locator('#stage').screenshot({path:join(folder,'clean-reference-18.png')});
        report.cleanFallback=cleanState;
      }finally{await clean.close();}
      const getProgress=()=>page.locator('#progress').evaluate(el=>parseFloat(el.style.width));
      const before=await getProgress();
      await page.locator('#pause').click();await page.waitForTimeout(450);
      const after=await getProgress();
      assert.ok(after>before,'play did not advance time');
      assert.equal(await page.locator('#pause').getAttribute('aria-label'),'일시정지');
      await page.locator('#pause').click();
      const held=await getProgress();await page.waitForTimeout(300);
      assert.equal(await getProgress(),held,'pause did not stop time');
      assert.equal(await page.locator('#pause').getAttribute('aria-label'),'재생');
      report.playPause='PASS';
    } else if(phase===18 && mobile) {
      // Genuine mobile browser touch input (not a synthetic desktop click).
      const getProgress=()=>page.locator('#progress').evaluate(el=>parseFloat(el.style.width));
      const before=await getProgress();
      await page.locator('#pause').tap();
      await page.waitForTimeout(350);
      assert.ok(await getProgress()>before,label+': mobile tap did not play');
      assert.equal(await page.locator('#pause').getAttribute('aria-label'),'일시정지');
      await page.locator('#pause').tap();
      const stopped=await getProgress();
      await page.waitForTimeout(260);
      assert.equal(await getProgress(),stopped,label+': mobile tap did not pause');
      assert.equal(await page.locator('#pause').getAttribute('aria-label'),'재생');
      report.mobileTouch=(report.mobileTouch||0)+1;
    }
    console.log('PASS '+label+' | '+colors.size+' colors | '+state.version);
  }finally{await context.close();}
}
try {
  browser=await chromium.launch({headless:true,channel:process.env.PW_BROWSER_CHANNEL||undefined,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
  for(const p of phases)await check(p,1280,720);
  await check(18,390,844,true);await check(18,844,390,true);
  report.conclusion='PASS';
} catch(e) {
  report.conclusion='FAIL';report.errors.push(String(e.stack||e));
  process.exitCode=1;console.error('Visual regression FAIL:',e);
} finally {
  await writeFile(join(folder,'report.json'),JSON.stringify(report,null,2));
  if(browser)await browser.close();
  await new Promise(resolve=>server.close(resolve));
}
