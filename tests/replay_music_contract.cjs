/* Behavioral soundtrack contract and source lifecycle guards (Node stdlib only). */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('docs/assets/app.js','utf8');
const begin=source.indexOf('const replaySoundtrack=(()=>{');
assert(begin>=0,'shared soundtrack manager exists');
const end=source.indexOf('\n})();',begin);
assert(end>begin,'manager has expected closing syntax');
const manager=source.slice(begin,end+'\n})();'.length);
class FakeAudio{
  constructor(src){this.src=src;this.paused=true;this.currentTime=0;this.volume=1;this.loop=false;this.playCount=0;this.handlers={};FakeAudio.instance=this}
  play(){this.paused=false;this.playCount++;return Promise.resolve()}
  pause(){this.paused=true}
  addEventListener(event,handler){this.handlers[event]=handler}
}
const storage=new Map();
const localStorage={getItem:key=>storage.has(key)?storage.get(key):null,setItem:(key,value)=>storage.set(key,String(value))};
const music={attributes:{},listeners:{},setAttribute(k,v){this.attributes[k]=v},addEventListener(k,v){this.listeners[k]=v},click(){this.listeners.click()}};
const volume={value:'0.35',listeners:{},addEventListener(k,v){this.listeners[k]=v},input(v){this.value=String(v);this.listeners.input({target:{value:String(v)}})}};
const note={hidden:true,textContent:''};
const host={querySelector(sel){return {'[data-replay-music]':music,'[data-replay-volume]':volume,'[data-replay-audio-note]':note}[sel]||null}};
const musicManager=vm.runInNewContext(manager+'; replaySoundtrack',{Audio:FakeAudio,localStorage,Number,Math});
const audio=FakeAudio.instance;
assert.equal(audio.src,'assets/satila-trail.mp3');
assert.equal(audio.loop,true,'soundtrack must loop after the race finishes');
assert.equal(audio.volume,0.35,'match Ultravasan Replay default volume');
musicManager.bind(host);
assert.equal(music.attributes['aria-pressed'],'true');
musicManager.start();
assert.equal(audio.paused,false,'start must begin music after user click');
music.click();
assert.equal(audio.paused,true,'mute pauses the audio');
assert.equal(storage.get('satila-music-enabled'),'false');
music.click();
assert.equal(audio.paused,false,'unmute restores music in active session');
volume.input(0.7);
assert.equal(audio.volume,0.7);
assert.equal(storage.get('satila-music-volume'),'0.7');
musicManager.pause();
assert.equal(audio.paused,true,'manual pause stops music');
musicManager.start();
audio.currentTime=22;
musicManager.close();
assert.equal(audio.paused,true,'closing dialog stops music');
assert.equal(audio.currentTime,0,'closing dialog resets track position');
musicManager.bind(host);
assert.equal(volume.value,'0.7','volume retained after reopening');
assert.equal(music.attributes['aria-pressed'],'true','enabled state retained after reopening');
assert(source.includes('if(next>=maxDistance)stop(false);'),'personal finish must keep soundtrack active');
assert(source.includes('if(next>=maxClock)stop(false);'),'duel finish must keep soundtrack active');
assert(source.includes("$('#profile-dialog').addEventListener('close',()=>{stop();replaySoundtrack.close()},{once:true})"),'personal popup close must stop sound');
assert(source.includes("dialog.addEventListener('close',()=>{stop();replaySoundtrack.close()},{once:true})"),'duel popup close must stop sound');
assert.equal((source.match(/data-replay-music aria-label=/g)||[]).length,2,'both players have music controls');
console.log('PASS: audio default, loop, start, mute/unmute, persistent volume, pause, close/reset, and both finished modal lifecycles');
