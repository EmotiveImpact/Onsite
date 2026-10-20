import {defineConfig,type ResolvedConfig} from 'vite'
import {readdir,unlink} from 'node:fs/promises'
import {resolve,join} from 'node:path'
let output='',root='';

export default defineConfig({
 optimizeDeps:{entries:['index.html','legacy.html']},
 server:{fs:{deny:['.git/**','research/**','assets/**','**/.env*']}},
 plugins:[{
  name:'onsite-runtime-assets-only',apply:'build',
  configResolved(config:ResolvedConfig){output=resolve(config.root,config.build.outDir);root=config.root},
  async closeBundle(){
   // Blender intermediates stay in the workspace, but never ship in a production copy.
   // A local build can otherwise include gitignored *.raw.glb files from public/.
   if(output===root||output===resolve(root,'public'))throw new Error('Build output must be separate from source assets');
   const folder=join(output,'models/heron-reach');
   const files=await readdir(folder).catch(()=>[]);
   await Promise.all(files.filter(f=>f.endsWith('.raw.glb')).map(f=>unlink(join(folder,f))));
  }
 }]
})
