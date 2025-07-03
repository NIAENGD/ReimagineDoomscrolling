(function(){"use strict";const be={env:{NODE_ENV:"production"}};function N(){const n=[".video-ads",".ytp-ad-module",".ytp-ad-player-overlay-layout",".ytp-ad-overlay-container"];for(const o of n){const i=document.querySelector(o);if(i){const a=window.getComputedStyle(i);if(a.display!=="none"&&a.visibility!=="hidden")return!0}}return!!document.querySelector(".ytp-skip-ad-button")}function te(){return new Promise((n,r)=>{let o=null;function i(){return new Promise(u=>{if(!N()){u();return}const d=setInterval(()=>{N()||(clearInterval(d),u())},1e3);setTimeout(()=>{clearInterval(d),u()},12e4)})}function a(){const u=document.querySelector(".ytp-subtitles-button");return u?(u.click(),setTimeout(()=>{u.click()},500),!0):!1}async function l(u){try{const d=await fetch(u);if(d.ok){const w=d.headers.get("content-type");let b;if(w&&w.includes("json")){const E=await d.json();b=ne(E)}else b=await d.text();o&&o.disconnect(),n(b)}}catch(d){console.error("Error fetching caption data:",d),r(d)}}"PerformanceObserver"in window&&(o=new PerformanceObserver(u=>{for(const d of u.getEntries())d.name.includes("timedtext")&&l(d.name)}),o.observe({entryTypes:["resource"]}));async function v(){let u=0;const d=20,w=setInterval(async()=>{if(u++,document.querySelector(".ytp-subtitles-button")){clearInterval(w);try{await i(),a()}catch(E){console.error("❌ Error waiting for ads:",E),r(E)}}else u>=d&&(clearInterval(w),r(new Error("Couldn't initialize caption retrieval")))},500)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",v):v(),setTimeout(()=>{o&&o.disconnect(),r(new Error("Timeout: No caption data received within 30 seconds"))},3e4)})}function ne(n){if(!(n!=null&&n.events))return[];const r=[];for(let o=0;o<n.events.length;o++){const i=n.events[o];if(!i.segs||i.segs.length===0)continue;const a=i.segs.map(d=>d.utf8||"").join("").trim();if(!a)continue;const l=i.tStartMs/1e3;let v;const u=n.events[o+1];u&&u.tStartMs?v=u.tStartMs/1e3:v=l+(i.dDurationMs||0)/1e3,r.push({text:a,start:l,end:v})}return re(r)}function re(n,r=10){var a;if(!(n!=null&&n.length))return[];const o=[];let i={start:n[0].start,end:n[0].start+r,text:[]};for(const l of n){l.start>=i.end&&(o.push({start:i.start,end:i.end,text:i.text.join(" ").trim()}),i={start:i.end,end:i.end+r,text:[]});const u=l.text.replace(/&#39;/g,"'");i.text.push(u)}return((a=i.text)==null?void 0:a.length)>0&&o.push({start:i.start,end:i.end,text:i.text.join(" ").trim()}),o}function oe(n){const r=Math.floor(n/3600),o=Math.floor(n%3600/60),i=Math.floor(n%60);return`${r?`${r.toString()}:`:""}${o.toString().padStart(2,"0")}:${i.toString().padStart(2,"0")}`}var q={exports:{}},s={};/**
 * @license React
 * react.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var G;function ie(){if(G)return s;G=1;var n=Symbol.for("react.element"),r=Symbol.for("react.portal"),o=Symbol.for("react.fragment"),i=Symbol.for("react.strict_mode"),a=Symbol.for("react.profiler"),l=Symbol.for("react.provider"),v=Symbol.for("react.context"),u=Symbol.for("react.forward_ref"),d=Symbol.for("react.suspense"),w=Symbol.for("react.memo"),b=Symbol.for("react.lazy"),E=Symbol.iterator;function T(e){return e===null||typeof e!="object"?null:(e=E&&e[E]||e["@@iterator"],typeof e=="function"?e:null)}var I={isMounted:function(){return!1},enqueueForceUpdate:function(){},enqueueReplaceState:function(){},enqueueSetState:function(){}},P=Object.assign,O={};function C(e,t,c){this.props=e,this.context=t,this.refs=O,this.updater=c||I}C.prototype.isReactComponent={},C.prototype.setState=function(e,t){if(typeof e!="object"&&typeof e!="function"&&e!=null)throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");this.updater.enqueueSetState(this,e,t,"setState")},C.prototype.forceUpdate=function(e){this.updater.enqueueForceUpdate(this,e,"forceUpdate")};function x(){}x.prototype=C.prototype;function _(e,t,c){this.props=e,this.context=t,this.refs=O,this.updater=c||I}var R=_.prototype=new x;R.constructor=_,P(R,C.prototype),R.isPureReactComponent=!0;var W=Array.isArray,Y=Object.prototype.hasOwnProperty,D={current:null},Z={key:!0,ref:!0,__self:!0,__source:!0};function X(e,t,c){var f,m={},h=null,g=null;if(t!=null)for(f in t.ref!==void 0&&(g=t.ref),t.key!==void 0&&(h=""+t.key),t)Y.call(t,f)&&!Z.hasOwnProperty(f)&&(m[f]=t[f]);var y=arguments.length-2;if(y===1)m.children=c;else if(1<y){for(var p=Array(y),k=0;k<y;k++)p[k]=arguments[k+2];m.children=p}if(e&&e.defaultProps)for(f in y=e.defaultProps,y)m[f]===void 0&&(m[f]=y[f]);return{$$typeof:n,type:e,key:h,ref:g,props:m,_owner:D.current}}function ye(e,t){return{$$typeof:n,type:e.type,key:t,ref:e.ref,props:e.props,_owner:e._owner}}function B(e){return typeof e=="object"&&e!==null&&e.$$typeof===n}function ge(e){var t={"=":"=0",":":"=2"};return"$"+e.replace(/[=:]/g,function(c){return t[c]})}var Q=/\/+/g;function z(e,t){return typeof e=="object"&&e!==null&&e.key!=null?ge(""+e.key):t.toString(36)}function $(e,t,c,f,m){var h=typeof e;(h==="undefined"||h==="boolean")&&(e=null);var g=!1;if(e===null)g=!0;else switch(h){case"string":case"number":g=!0;break;case"object":switch(e.$$typeof){case n:case r:g=!0}}if(g)return g=e,m=m(g),e=f===""?"."+z(g,0):f,W(m)?(c="",e!=null&&(c=e.replace(Q,"$&/")+"/"),$(m,t,c,"",function(k){return k})):m!=null&&(B(m)&&(m=ye(m,c+(!m.key||g&&g.key===m.key?"":(""+m.key).replace(Q,"$&/")+"/")+e)),t.push(m)),1;if(g=0,f=f===""?".":f+":",W(e))for(var y=0;y<e.length;y++){h=e[y];var p=f+z(h,y);g+=$(h,t,c,p,m)}else if(p=T(e),typeof p=="function")for(e=p.call(e),y=0;!(h=e.next()).done;)h=h.value,p=f+z(h,y++),g+=$(h,t,c,p,m);else if(h==="object")throw t=String(e),Error("Objects are not valid as a React child (found: "+(t==="[object Object]"?"object with keys {"+Object.keys(e).join(", ")+"}":t)+"). If you meant to render a collection of children, use an array instead.");return g}function M(e,t,c){if(e==null)return e;var f=[],m=0;return $(e,f,"","",function(h){return t.call(c,h,m++)}),f}function ve(e){if(e._status===-1){var t=e._result;t=t(),t.then(function(c){(e._status===0||e._status===-1)&&(e._status=1,e._result=c)},function(c){(e._status===0||e._status===-1)&&(e._status=2,e._result=c)}),e._status===-1&&(e._status=0,e._result=t)}if(e._status===1)return e._result.default;throw e._result}var S={current:null},F={transition:null},we={ReactCurrentDispatcher:S,ReactCurrentBatchConfig:F,ReactCurrentOwner:D};function ee(){throw Error("act(...) is not supported in production builds of React.")}return s.Children={map:M,forEach:function(e,t,c){M(e,function(){t.apply(this,arguments)},c)},count:function(e){var t=0;return M(e,function(){t++}),t},toArray:function(e){return M(e,function(t){return t})||[]},only:function(e){if(!B(e))throw Error("React.Children.only expected to receive a single React element child.");return e}},s.Component=C,s.Fragment=o,s.Profiler=a,s.PureComponent=_,s.StrictMode=i,s.Suspense=d,s.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED=we,s.act=ee,s.cloneElement=function(e,t,c){if(e==null)throw Error("React.cloneElement(...): The argument must be a React element, but you passed "+e+".");var f=P({},e.props),m=e.key,h=e.ref,g=e._owner;if(t!=null){if(t.ref!==void 0&&(h=t.ref,g=D.current),t.key!==void 0&&(m=""+t.key),e.type&&e.type.defaultProps)var y=e.type.defaultProps;for(p in t)Y.call(t,p)&&!Z.hasOwnProperty(p)&&(f[p]=t[p]===void 0&&y!==void 0?y[p]:t[p])}var p=arguments.length-2;if(p===1)f.children=c;else if(1<p){y=Array(p);for(var k=0;k<p;k++)y[k]=arguments[k+2];f.children=y}return{$$typeof:n,type:e.type,key:m,ref:h,props:f,_owner:g}},s.createContext=function(e){return e={$$typeof:v,_currentValue:e,_currentValue2:e,_threadCount:0,Provider:null,Consumer:null,_defaultValue:null,_globalName:null},e.Provider={$$typeof:l,_context:e},e.Consumer=e},s.createElement=X,s.createFactory=function(e){var t=X.bind(null,e);return t.type=e,t},s.createRef=function(){return{current:null}},s.forwardRef=function(e){return{$$typeof:u,render:e}},s.isValidElement=B,s.lazy=function(e){return{$$typeof:b,_payload:{_status:-1,_result:e},_init:ve}},s.memo=function(e,t){return{$$typeof:w,type:e,compare:t===void 0?null:t}},s.startTransition=function(e){var t=F.transition;F.transition={};try{e()}finally{F.transition=t}},s.unstable_act=ee,s.useCallback=function(e,t){return S.current.useCallback(e,t)},s.useContext=function(e){return S.current.useContext(e)},s.useDebugValue=function(){},s.useDeferredValue=function(e){return S.current.useDeferredValue(e)},s.useEffect=function(e,t){return S.current.useEffect(e,t)},s.useId=function(){return S.current.useId()},s.useImperativeHandle=function(e,t,c){return S.current.useImperativeHandle(e,t,c)},s.useInsertionEffect=function(e,t){return S.current.useInsertionEffect(e,t)},s.useLayoutEffect=function(e,t){return S.current.useLayoutEffect(e,t)},s.useMemo=function(e,t){return S.current.useMemo(e,t)},s.useReducer=function(e,t,c){return S.current.useReducer(e,t,c)},s.useRef=function(e){return S.current.useRef(e)},s.useState=function(e){return S.current.useState(e)},s.useSyncExternalStore=function(e,t,c){return S.current.useSyncExternalStore(e,t,c)},s.useTransition=function(){return S.current.useTransition()},s.version="18.3.1",s}var U;function se(){return U||(U=1,q.exports=ie()),q.exports}se();const j=[{id:"key-points-summary",name:"Summary with Key Points & Takeaways",isDefault:!0,content:`Please provide a summary of the following content:
1. First, give a concise one-sentence summary that captures the core message/theme
2. Then, share a breakdown of the main topics discussed. For each topic:
    - Use suitable emojis for the subtitle of each topic
    - Expound very briefly on what was discussed on each topic
    - Include any notable quotes or statistics
    - Keep the tone of the content. Be conversational. How a friend would give the summary.
3. End with a brief takeaways
4. Don't start the text with "Let me...", or "Here is the summary...". Just give the results.`},{id:"short-form",name:"Shortform-Like Summary (Detailed)",content:`Summarize the following how Shortlist or Blinkist would.
Keep the tone of the content. Keep it conversational.
Break the headers using relevant dynamic emojis.
Go beyond the title in giving the summary, look through entire content.
Sprinkle in quotes or excerpts to better link the summary to the content.
Don't start the text with "Let me...", or "Here is the summary...". Just give the results.`},{id:"youtube",name:"For Youtube",content:`For each chapter highlighted, provide a summary on what was discussed based on the transcript.
For each chapter summary;
- Start each topic subtitle with a relevant emoji
- Expound very briefly on what was discussed on each topic
- Include any notable quotes or statistics
- Keep the tone of the content. Be conversational.
Otherwise (if no chapters), share a breakdown of the main topics discussed. For each topic:
    - Start each topic subtitle with a relevant emoji
    - Expound very briefly on what was discussed on each topic
    - Include any notable quotes or statistics
    - Keep the tone of the content.`},{id:"simple",name:"Simple language",content:`Explain the following text with language:
- Simple and clear language with a conversational tone.
- Cover all the major and interesting topics discussed.
- Break the headers using relevant dynamic emojis.
- Don't start the text with "Let me...", or "Here is the summary...". Just give the results.`},{id:"5-10-points",name:"5-10 Key Points",content:`Please provide the 5-10 most important points from the text.
Use bullet points and emojis to break up the text.
Focus on the key points and avoid summarizing everything.
Don't include any additional information, focus on the key points.`}];var L=(n=>(n.CLAUDE="claude",n.CHATGPT="chatgpt",n.GEMINI="gemini",n.DEEPSEEK="deepseek",n.GROK="grok",n))(L||{});const H={[L.CHATGPT]:{id:L.CHATGPT,name:"ChatGPT",url:"https://chatgpt.com",icon:"/assets/icons/chatgpt-logo.png",characterLimit:15e3,premiumCharacterLimit:2e5},[L.CLAUDE]:{id:L.CLAUDE,name:"Claude",url:"https://claude.ai/new",icon:"/assets/icons/claude-logo.svg",characterLimit:2e4,premiumCharacterLimit:25e4},[L.DEEPSEEK]:{id:L.DEEPSEEK,name:"DeepSeek",url:"https://chat.deepseek.com",icon:"/assets/icons/deepseek-logo.png",characterLimit:2e5,premiumCharacterLimit:2e5},[L.GEMINI]:{id:L.GEMINI,name:"Gemini",url:"https://gemini.google.com/app",icon:"/assets/icons/gemini-logo.png",characterLimit:32e3,premiumCharacterLimit:25e4},[L.GROK]:{id:L.GROK,name:"Grok",url:"https://grok.com",icon:"/assets/icons/grok-logo.png",characterLimit:1e5,premiumCharacterLimit:2e5}},A=H[L.CHATGPT],ae=async()=>{try{const n=await chrome.storage.sync.get({premiumServices:null,aiServiceId:A.id}),r=H[n.aiServiceId],i=(n.premiumServices||{})[n.aiServiceId]?r==null?void 0:r.premiumCharacterLimit:r==null?void 0:r.characterLimit;return{...r,characterLimit:i}}catch(n){return console.error("Failed to get AI Service:",n),{...A,characterLimit:A.characterLimit}}},ue=async()=>{try{return(await chrome.storage.sync.get({prompts:j})).prompts.find(o=>o.isDefault)||j[0]}catch(n){return console.error("Failed to get default prompt:",n),j[0]}},ce={characterLimit:2e4,initialContentRatio:.4,chunkSize:300,minChunksPerSegment:3};function le(n,r={}){const o={...ce,...r};if(n.length<=o.characterLimit)return n;const i=me(n,o.chunkSize),a=[];let l=0;const v=Math.floor(o.characterLimit*o.initialContentRatio);let u=0;for(;u<i.length&&l<v;){const b=i[u];if(l+b.length<=v)a.push(b),l+=b.length;else{const E=v-l;if(E>10){const T=b.slice(0,E);a.push(T),l+=E}break}u++}const d=o.characterLimit-l,w=i.slice(u);if(w.length>0){const b=fe(w)/w.length,E=Math.floor(d/(b*o.minChunksPerSegment)),T=de(w.length,E);for(const I of T){if(l>=o.characterLimit)break;const P=Math.floor(w.length*I),O=Math.min(o.minChunksPerSegment,w.length-P);for(let C=0;C<O;C++){const x=w[P+C],_=o.characterLimit-l;if(x.length<=_)a.push(x),l+=x.length;else if(_>10){const R=x.slice(0,_);a.push(R),l+=_;break}}}}return a.join("").replace(/[\n\r]+/g," ").replace(/\s{2,}/g," ").trim()}function me(n,r){const o=[];let i=0;for(;i<n.length;){if(i+r>=n.length){o.push(n.slice(i).trim());break}let a=n.slice(i,i+r);const l=a.lastIndexOf(" ");a=a.slice(0,l),i+=l+1,o.push(a.trim())}return o}function fe(n){return n.reduce((r,o)=>r+o.length,0)}function de(n,r){if(n<=0||r<=0)return[];const o=[],i=1/(r+1);for(let a=1;a<=r;a++)o.push(i*a);return o}function K(){const n=document.createElement("style");if(n.textContent=`
    .ytp-pause-overlay-container {
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
    }

    .ytp-pause-overlay {
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }

    /* Hide sparkle button when YouTube controls are auto-hidden */
    .ytp-autohide .justtldr-embed-summarize-btn {
      display: none !important;
    }

    /* Hide button when video is in unstarted mode */
    .unstarted-mode .justtldr-embed-summarize-btn {
      display: none !important;
    }

    /* Button state styles */
    .justtldr-embed-summarize-btn.loading svg {
      animation: pulse 1.5s ease-in-out infinite;
    }

    .justtldr-embed-summarize-btn.error svg {
      fill: rgba(255,255,255,0.4) !important;
    }

    .justtldr-embed-summarize-btn.error svg path {
      fill: rgba(255,255,255,0.4) !important;
    }
  `,document.head)document.head.appendChild(n);else if(document.documentElement)document.documentElement.appendChild(n);else{setTimeout(K,500);return}}K();async function pe(){return{title:"",chapters:"",transcript:await te()}}async function he(){var n;try{const r=await pe();if(!((n=r==null?void 0:r.transcript)!=null&&n.length))throw new Error("No transcript available for this video");const{url:o,characterLimit:i}=await ae(),a=await ue(),l=r.transcript.map(b=>`(${oe(b.start)}) ${b.text}`).join(" "),u=`First, carefully analyze the following transcript. ${(a==null?void 0:a.content)||j[0].content}

Transcript: "${l}"`,d=i&&l.length>i?le(u,{characterLimit:i}):u;await chrome.runtime.sendMessage({type:"STORE_TEXT",text:d});const w=`${o}?justTLDR`;window.open(w,"_blank")}catch(r){throw console.error("[justTLDR] EmbedOverlayRemover: Error in getSummary:",r),r}}function V(){if(document.querySelector(".justtldr-embed-summarize-btn"))return;const n=document.querySelector(".ytp-chrome-top-buttons");if(!n)return;const r=document.createElement("button");r.className="justtldr-embed-summarize-btn ytp-button",r.setAttribute("title","Summarize with AI"),r.setAttribute("data-tooltip-opaque","true"),r.innerHTML=`
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
      <svg width="24" height="36" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" style="margin-bottom: 4px;">
        <!-- Main 4-point star, narrow and white -->
        <path
          d="M12 1.5
             C13.5 7.5, 15.75 11.25, 22.5 12
             C15.75 12.75, 13.5 16.5, 12 22.5
             C10.5 16.5, 8.25 12.75, 1.5 12
             C8.25 11.25, 10.5 7.5, 12 1.5Z"
          fill="white"
        />
        <!-- Top-right mini star -->
        <path
          d="M18.75 5.25
             L19.125 6.375
             L20.25 6.75
             L19.125 7.125
             L18.75 8.25
             L18.375 7.125
             L17.25 6.75
             L18.375 6.375
             L18.75 5.25Z"
          fill="white"
        />
        <!-- Bottom-left mini star -->
        <path
          d="M5.25 17.25
             L5.625 18
             L6.375 18.375
             L5.625 18.75
             L5.25 19.5
             L4.875 18.75
             L4.125 18.375
             L4.875 18
             L5.25 17.25Z"
          fill="white"
        />
      </svg>
    </div>
  `,r.style.cssText=`
    background: transparent;
    border: none;
    color: white;
    cursor: pointer;
    display: inline-block;
    font-size: inherit;
    height: 62px;
    margin: 0;
    opacity: 0.9;
    outline: none;
    overflow: hidden;
    padding: 0;
    position: relative;
    text-align: center;
    touch-action: manipulation;
    width: 64px;
    transition: opacity 0.1s ease;
  `,r.addEventListener("mouseenter",()=>{r.style.opacity="1"}),r.addEventListener("mouseleave",()=>{r.style.opacity="0.9"}),r.addEventListener("click",async()=>{try{r.disabled=!0,r.classList.add("loading"),await he(),r.classList.remove("loading"),r.disabled=!1}catch(o){console.error("[justTLDR] EmbedOverlayRemover: Error:",o),r.classList.remove("loading"),r.classList.add("error"),setTimeout(()=>{r.classList.remove("error"),r.disabled=!1},3e3)}}),n.insertBefore(r,n.firstChild)}function J(){let n=0;const r=30,o=()=>{n++,document.querySelector(".ytp-chrome-top-buttons")?V():n<r&&setTimeout(o,1e3)};o();const i=new MutationObserver(a=>{for(const l of a)if(l.type==="childList"){for(const v of l.addedNodes)if(v.nodeType===Node.ELEMENT_NODE){const u=v;if(u.querySelector(".ytp-chrome-top-buttons")||u.classList.contains("ytp-chrome-top-buttons")){i.disconnect(),setTimeout(V,300);return}}}});i.observe(document.body||document.documentElement,{childList:!0,subtree:!0}),setTimeout(()=>{i.disconnect()},r*1e3)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",J):J()})();
