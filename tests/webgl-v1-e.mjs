import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { chromium } from 'playwright';
import { PNG } from 'pngjs';

const folder=join(process.cwd(),'test-results','v1-e');
await mkdir(folder,{recursive:true});
const report={name:'StarCraft Diorama v1.0-E',checks:[],errors:[],conclusion:'INCOMPLETE'};
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
        error:gl?.getError(),dimensions:gl?[gl.drawingBufferWidth,gl.drawingBufferHeight]:null,
        fallback:getComputedStyle(document.querySelector('#fallback')).display,
        progress:parseFloat(document.querySelector('#progress').style.width),
        pause:document.querySelector('#pause').getAttribute('aria-label')
      };
    });
    assert.ok(state.webgl2,label+': WebGL2 not available');
    assert.equal(state.error,0,label+': GPU error');
    assert.deepEqual(state.dimensions,[width,height],label+': canvas resolution');
    assert.equal(state.fallback,'none',label+': fallback shown');
    assert.equal(state.pause,'재생',label+': pause initial state');
    assert.ok(Math.abs(state.progress-phase/35*100)<.8,label+': incorrect phase progress');
    assert.deepEqual(errors,[],label+': uncaught JavaScript errors');
    // A real screen-space check: the highest old Armory chimney must remain inside
    // both desktop and landscape-phone viewports (prior version cropped it).
    const topLandmarkY=await page.evaluate(()=>project3(-4.21,4.25,-3.69)[1]);
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
    if(phase===18 && width===1280){
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
  browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
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
