"""Headless Chromium checks for sprite loader independent of unavailable WebGL2."""
import asyncio
import base64
import io
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright

HERE=Path(__file__).resolve()
HTML=(HERE.parents[1]/'original.html').read_text()
MODULE=HTML.split('const assetState=',1)[1].split("const btn=$('pause');",1)[0]
SCRIPT="const $=id=>document.getElementById(id);const q=new URLSearchParams(location.search);const assetState="+MODULE

def png_col(color):
    buff=io.BytesIO();Image.new('RGBA',(20,24),color).save(buff,format='PNG');return buff.getvalue()

async def main():
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True)
        page=await browser.new_page()
        errors=[];page.on('pageerror',lambda ex:errors.append(str(ex)))
        await page.set_content('''<div id="assetMode"></div><button id="assetBtn">import</button><button id="spriteToggle"></button><input id="assetInput" type="file" multiple />''')
        await page.add_script_tag(content=SCRIPT)
        # Test full multi-frame folder import: four names -> one key with four frames.
        payloads=[{'name':f'marine_{i:04d}.png','mimeType':'image/png','buffer':png_col(col)} for i,col in enumerate([(255,0,0),(0,255,0),(0,0,255),(255,255,0)])]
        await page.locator('#assetInput').set_input_files(payloads)
        await page.wait_for_timeout(450)
        imported=await page.evaluate('()=>({count:assetState.sprites.marine?.frames.length,keys:Object.keys(assetState.sprites),mode:assetState.enabled})')
        assert imported=={'count':4,'keys':['marine'],'mode':True},imported
        seq=await page.evaluate('''()=>{
          assetState.meta.marine={fps:2,states:{idle:[0,1,0,2],react:[3]}};
          const frames=assetState.sprites.marine.frames;
          const selected=(state,t)=>frames.indexOf(pickSprite('marine',state,t).img);
          return {idle:[selected('idle',0),selected('idle',.5),selected('idle',1),selected('idle',1.5)],react:selected('react',11)};
        }''')
        assert seq=={'idle':[0,1,0,2],'react':3},seq
        await page.locator('#spriteToggle').click()
        assert not (await page.evaluate('()=>assetState.enabled'))
        await page.locator('#spriteToggle').click()
        assert await page.evaluate('()=>assetState.enabled')
        # Error fallback: missing images must not remove a previously loaded valid pack.
        state=await page.evaluate('''async()=>{
          await applyManifest({sprites:{marine:{src:'missing_file.png'}}});
          return {enabled:assetState.enabled,count:Object.keys(assetState.sprites).length};
        }''')
        assert state=={'enabled':True,'count':1},state
        assert not errors,errors
        print('Chromium: PNG sequence import, animation states, 3D switch, error fallback: PASS')
        await browser.close()

asyncio.run(main())