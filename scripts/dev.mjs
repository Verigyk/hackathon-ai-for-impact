/** Single local launcher. Binds both services to loopback and shuts down its children. */
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { join, dirname, delimiter } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=dirname(dirname(fileURLToPath(import.meta.url)));
const bundled=process.env.LOCALAPPDATA ? join(process.env.USERPROFILE,'.cache','codex-runtimes','codex-primary-runtime','dependencies','python','python.exe') : '';
const python=process.env.PYTHON_BIN || (existsSync(bundled)?bundled:(process.platform==='win32'?'python':'python3'));
const env={...process.env,PYTHONPATH:[join(root,'.python-deps'),root,process.env.PYTHONPATH||''].filter(Boolean).join(delimiter),PYTHONUTF8:'1'};
const backend=spawn(python,[join(root,'scripts','serve_backend.py')],{cwd:root,env,stdio:'inherit',windowsHide:true});
const frontend=spawn(process.execPath,[join(root,'node_modules','next','dist','bin','next'),'dev','--hostname','127.0.0.1','--port','3000'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const stop=()=>{backend.kill();frontend.kill();};
process.on('SIGINT',()=>{stop();process.exit(0);});process.on('SIGTERM',()=>{stop();process.exit(0);});
for(const child of [backend,frontend]){child.on('error',error=>{console.error(error.message);stop();process.exit(1);});child.on('exit',code=>{if(code){stop();process.exit(code);}});}
console.log('\nÉchappée → http://127.0.0.1:3000\nAPI → http://127.0.0.1:8000/docs\nCtrl+C pour arrêter les deux services.\n');
