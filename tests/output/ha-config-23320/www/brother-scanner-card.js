function t(t,e,s,i){var n,o=arguments.length,r=o<3?e:null===i?i=Object.getOwnPropertyDescriptor(e,s):i;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)r=Reflect.decorate(t,e,s,i);else for(var a=t.length-1;a>=0;a--)(n=t[a])&&(r=(o<3?n(r):o>3?n(e,s,r):n(e,s))||r);return o>3&&r&&Object.defineProperty(e,s,r),r}"function"==typeof SuppressedError&&SuppressedError;const e=globalThis,s=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,i=Symbol(),n=new WeakMap;let o=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==i)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(s&&void 0===t){const s=void 0!==e&&1===e.length;s&&(t=n.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&n.set(e,t))}return t}toString(){return this.cssText}};const r=(t,...e)=>{const s=1===t.length?t[0]:e.reduce((e,s,i)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+t[i+1],t[0]);return new o(s,t,i)},a=s?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return(t=>new o("string"==typeof t?t:t+"",void 0,i))(e)})(t):t,{is:c,defineProperty:l,getOwnPropertyDescriptor:h,getOwnPropertyNames:d,getOwnPropertySymbols:p,getPrototypeOf:u}=Object,f=globalThis,g=f.trustedTypes,m=g?g.emptyScript:"",_=f.reactiveElementPolyfillSupport,$=(t,e)=>t,b={toAttribute(t,e){switch(e){case Boolean:t=t?m:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let s=t;switch(e){case Boolean:s=null!==t;break;case Number:s=null===t?null:Number(t);break;case Object:case Array:try{s=JSON.parse(t)}catch(t){s=null}}return s}},y=(t,e)=>!c(t,e),v={attribute:!0,type:String,converter:b,reflect:!1,useDefault:!1,hasChanged:y};Symbol.metadata??=Symbol("metadata"),f.litPropertyMetadata??=new WeakMap;let w=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=v){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const s=Symbol(),i=this.getPropertyDescriptor(t,s,e);void 0!==i&&l(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){const{get:i,set:n}=h(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:i,set(e){const o=i?.call(this);n?.call(this,e),this.requestUpdate(t,o,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??v}static _$Ei(){if(this.hasOwnProperty($("elementProperties")))return;const t=u(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty($("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty($("properties"))){const t=this.properties,e=[...d(t),...p(t)];for(const s of e)this.createProperty(s,t[s])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,s]of e)this.elementProperties.set(t,s)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const s=this._$Eu(t,e);void 0!==s&&this._$Eh.set(s,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const s=new Set(t.flat(1/0).reverse());for(const t of s)e.unshift(a(t))}else void 0!==t&&e.push(a(t));return e}static _$Eu(t,e){const s=e.attribute;return!1===s?void 0:"string"==typeof s?s:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,i)=>{if(s)t.adoptedStyleSheets=i.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const s of i){const i=document.createElement("style"),n=e.litNonce;void 0!==n&&i.setAttribute("nonce",n),i.textContent=s.cssText,t.appendChild(i)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){const s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(void 0!==i&&!0===s.reflect){const n=(void 0!==s.converter?.toAttribute?s.converter:b).toAttribute(e,s.type);this._$Em=t,null==n?this.removeAttribute(i):this.setAttribute(i,n),this._$Em=null}}_$AK(t,e){const s=this.constructor,i=s._$Eh.get(t);if(void 0!==i&&this._$Em!==i){const t=s.getPropertyOptions(i),n="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:b;this._$Em=i;const o=n.fromAttribute(e,t.type);this[i]=o??this._$Ej?.get(i)??o,this._$Em=null}}requestUpdate(t,e,s,i=!1,n){if(void 0!==t){const o=this.constructor;if(!1===i&&(n=this[t]),s??=o.getPropertyOptions(t),!((s.hasChanged??y)(n,e)||s.useDefault&&s.reflect&&n===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,s))))return;this.C(t,e,s)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:n},o){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),!0!==n||void 0!==o)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),!0===i&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,s]of t){const{wrapped:t}=s,i=this[e];!0!==t||this._$AL.has(e)||void 0===i||this.C(e,void 0,s,i)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[$("elementProperties")]=new Map,w[$("finalized")]=new Map,_?.({ReactiveElement:w}),(f.reactiveElementVersions??=[]).push("2.1.2");const A=globalThis,x=t=>t,S=A.trustedTypes,E=S?S.createPolicy("lit-html",{createHTML:t=>t}):void 0,C="$lit$",k=`lit$${Math.random().toFixed(9).slice(2)}$`,P="?"+k,O=`<${P}>`,U=document,R=()=>U.createComment(""),T=t=>null===t||"object"!=typeof t&&"function"!=typeof t,M=Array.isArray,N="[ \t\n\f\r]",H=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,z=/-->/g,D=/>/g,j=RegExp(`>|${N}(?:([^\\s"'>=/]+)(${N}*=${N}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),L=/'/g,B=/"/g,I=/^(?:script|style|textarea|title)$/i,q=(t=>(e,...s)=>({_$litType$:t,strings:e,values:s}))(1),W=Symbol.for("lit-noChange"),V=Symbol.for("lit-nothing"),F=new WeakMap,J=U.createTreeWalker(U,129);function K(t,e){if(!M(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==E?E.createHTML(e):e}const Q=(t,e)=>{const s=t.length-1,i=[];let n,o=2===e?"<svg>":3===e?"<math>":"",r=H;for(let e=0;e<s;e++){const s=t[e];let a,c,l=-1,h=0;for(;h<s.length&&(r.lastIndex=h,c=r.exec(s),null!==c);)h=r.lastIndex,r===H?"!--"===c[1]?r=z:void 0!==c[1]?r=D:void 0!==c[2]?(I.test(c[2])&&(n=RegExp("</"+c[2],"g")),r=j):void 0!==c[3]&&(r=j):r===j?">"===c[0]?(r=n??H,l=-1):void 0===c[1]?l=-2:(l=r.lastIndex-c[2].length,a=c[1],r=void 0===c[3]?j:'"'===c[3]?B:L):r===B||r===L?r=j:r===z||r===D?r=H:(r=j,n=void 0);const d=r===j&&t[e+1].startsWith("/>")?" ":"";o+=r===H?s+O:l>=0?(i.push(a),s.slice(0,l)+C+s.slice(l)+k+d):s+k+(-2===l?e:d)}return[K(t,o+(t[s]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),i]};class Z{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let n=0,o=0;const r=t.length-1,a=this.parts,[c,l]=Q(t,e);if(this.el=Z.createElement(c,s),J.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(i=J.nextNode())&&a.length<r;){if(1===i.nodeType){if(i.hasAttributes())for(const t of i.getAttributeNames())if(t.endsWith(C)){const e=l[o++],s=i.getAttribute(t).split(k),r=/([.?@])?(.*)/.exec(e);a.push({type:1,index:n,name:r[2],strings:s,ctor:"."===r[1]?et:"?"===r[1]?st:"@"===r[1]?it:tt}),i.removeAttribute(t)}else t.startsWith(k)&&(a.push({type:6,index:n}),i.removeAttribute(t));if(I.test(i.tagName)){const t=i.textContent.split(k),e=t.length-1;if(e>0){i.textContent=S?S.emptyScript:"";for(let s=0;s<e;s++)i.append(t[s],R()),J.nextNode(),a.push({type:2,index:++n});i.append(t[e],R())}}}else if(8===i.nodeType)if(i.data===P)a.push({type:2,index:n});else{let t=-1;for(;-1!==(t=i.data.indexOf(k,t+1));)a.push({type:7,index:n}),t+=k.length-1}n++}}static createElement(t,e){const s=U.createElement("template");return s.innerHTML=t,s}}function G(t,e,s=t,i){if(e===W)return e;let n=void 0!==i?s._$Co?.[i]:s._$Cl;const o=T(e)?void 0:e._$litDirective$;return n?.constructor!==o&&(n?._$AO?.(!1),void 0===o?n=void 0:(n=new o(t),n._$AT(t,s,i)),void 0!==i?(s._$Co??=[])[i]=n:s._$Cl=n),void 0!==n&&(e=G(t,n._$AS(t,e.values),n,i)),e}class X{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??U).importNode(e,!0);J.currentNode=i;let n=J.nextNode(),o=0,r=0,a=s[0];for(;void 0!==a;){if(o===a.index){let e;2===a.type?e=new Y(n,n.nextSibling,this,t):1===a.type?e=new a.ctor(n,a.name,a.strings,this,t):6===a.type&&(e=new nt(n,this,t)),this._$AV.push(e),a=s[++r]}o!==a?.index&&(n=J.nextNode(),o++)}return J.currentNode=U,i}p(t){let e=0;for(const s of this._$AV)void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}}class Y{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=V,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=G(this,t,e),T(t)?t===V||null==t||""===t?(this._$AH!==V&&this._$AR(),this._$AH=V):t!==this._$AH&&t!==W&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>M(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==V&&T(this._$AH)?this._$AA.nextSibling.data=t:this.T(U.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:s}=t,i="number"==typeof s?this._$AC(t):(void 0===s.el&&(s.el=Z.createElement(K(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{const t=new X(i,this),s=t.u(this.options);t.p(e),this.T(s),this._$AH=t}}_$AC(t){let e=F.get(t.strings);return void 0===e&&F.set(t.strings,e=new Z(t)),e}k(t){M(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let s,i=0;for(const n of t)i===e.length?e.push(s=new Y(this.O(R()),this.O(R()),this,this.options)):s=e[i],s._$AI(n),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=x(t).nextSibling;x(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class tt{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,n){this.type=1,this._$AH=V,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=n,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=V}_$AI(t,e=this,s,i){const n=this.strings;let o=!1;if(void 0===n)t=G(this,t,e,0),o=!T(t)||t!==this._$AH&&t!==W,o&&(this._$AH=t);else{const i=t;let r,a;for(t=n[0],r=0;r<n.length-1;r++)a=G(this,i[s+r],e,r),a===W&&(a=this._$AH[r]),o||=!T(a)||a!==this._$AH[r],a===V?t=V:t!==V&&(t+=(a??"")+n[r+1]),this._$AH[r]=a}o&&!i&&this.j(t)}j(t){t===V?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class et extends tt{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===V?void 0:t}}class st extends tt{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==V)}}class it extends tt{constructor(t,e,s,i,n){super(t,e,s,i,n),this.type=5}_$AI(t,e=this){if((t=G(this,t,e,0)??V)===W)return;const s=this._$AH,i=t===V&&s!==V||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,n=t!==V&&(s===V||i);i&&this.element.removeEventListener(this.name,this,s),n&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class nt{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){G(this,t)}}const ot=A.litHtmlPolyfillSupport;ot?.(Z,Y),(A.litHtmlVersions??=[]).push("3.3.3");const rt=globalThis;class at extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,s)=>{const i=s?.renderBefore??e;let n=i._$litPart$;if(void 0===n){const t=s?.renderBefore??null;i._$litPart$=n=new Y(e.insertBefore(R(),t),t,void 0,s??{})}return n._$AI(t),n})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return W}}at._$litElement$=!0,at.finalized=!0,rt.litElementHydrateSupport?.({LitElement:at});const ct=rt.litElementPolyfillSupport;ct?.({LitElement:at}),(rt.litElementVersions??=[]).push("4.2.2");const lt={attribute:!0,type:String,converter:b,reflect:!1,hasChanged:y},ht=(t=lt,e,s)=>{const{kind:i,metadata:n}=s;let o=globalThis.litPropertyMetadata.get(n);if(void 0===o&&globalThis.litPropertyMetadata.set(n,o=new Map),"setter"===i&&((t=Object.create(t)).wrapped=!0),o.set(s.name,t),"accessor"===i){const{name:i}=s;return{set(s){const n=e.get.call(this);e.set.call(this,s),this.requestUpdate(i,n,t,!0,s)},init(e){return void 0!==e&&this.C(i,void 0,t,e),e}}}if("setter"===i){const{name:i}=s;return function(s){const n=this[i];e.call(this,s),this.requestUpdate(i,n,t,!0,s)}}throw Error("Unsupported decorator location: "+i)};function dt(t){return(e,s)=>"object"==typeof s?ht(t,e,s):((t,e,s)=>{const i=e.hasOwnProperty(s);return e.constructor.createProperty(s,t),i?Object.getOwnPropertyDescriptor(e,s):void 0})(t,e,s)}function pt(t){return dt({...t,state:!0,attribute:!1})}const ut=["file","ocr","email","image"];class ft extends at{constructor(){super(...arguments),this.labels={entity:"Scanner state sensor",name:"Name (optional)",show_image:"Show picture",show_buttons:"Show scan buttons",show_selects:"Show resolution / mode / source",show_last_scan:"Show last scan",show_link:"Link to the web UI",compact:"Compact",image:"Picture URL (optional, overrides the integration)",buttons:"Buttons to show (empty: all enabled actions)"}}setConfig(t){this.config=t}get schema(){return[{name:"entity",required:!0,selector:{entity:{domain:"sensor",integration:"brother_scanner"}}},{name:"name",selector:{text:{}}},{type:"grid",name:"",schema:[{name:"show_image",selector:{boolean:{}}},{name:"show_buttons",selector:{boolean:{}}},{name:"show_selects",selector:{boolean:{}}},{name:"show_last_scan",selector:{boolean:{}}},{name:"show_link",selector:{boolean:{}}},{name:"compact",selector:{boolean:{}}}]},{name:"image",selector:{text:{}}},{name:"buttons",selector:{select:{multiple:!0,mode:"list",options:ut.map(t=>({value:t,label:t}))}}}]}render(){if(!this.hass||!this.config)return V;const t={show_image:!0,show_buttons:!0,show_selects:!1,show_last_scan:!0,show_link:!0,compact:!1,...this.config};return q`
      <ha-form
        .hass=${this.hass}
        .data=${t}
        .schema=${this.schema}
        .computeLabel=${t=>this.labels[t.name]||t.name}
        @value-changed=${this.valueChanged}
      ></ha-form>
    `}valueChanged(t){const e={...t.detail.value};Array.isArray(e.buttons)&&0===e.buttons.length&&delete e.buttons,""===e.image&&delete e.image,""===e.name&&delete e.name,this.config=e,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:e},bubbles:!0,composed:!0}))}}ft.styles=r`
    ha-form {
      display: block;
    }
  `,t([dt({attribute:!1})],ft.prototype,"hass",void 0),t([pt()],ft.prototype,"config",void 0),customElements.define("brother-scanner-card-editor",ft);const gt={idle:"mdi:emoticon-happy-outline",scanning:"mdi:scanner",waiting_for_rear:"mdi:timer-sand",converting:"mdi:cog-outline",ocr:"mdi:brain",unreachable:"mdi:lan-disconnect",unavailable:"mdi:cloud-off-outline",unknown:"mdi:help-circle-outline"},mt={idle:"Ready",scanning:"Scanning…",waiting_for_rear:"Waiting for rear pages",converting:"Converting…",ocr:"OCR running",unreachable:"Scanner unreachable",unavailable:"Container unavailable",unknown:"Unknown"},_t={file:"mdi:file-document-outline",ocr:"mdi:text-recognition",email:"mdi:book-open-page-variant",image:"mdi:image-outline"};class $t extends at{constructor(){super(...arguments),this.busy=null,this.error=null,this.now=Date.now()}static getConfigElement(){return document.createElement("brother-scanner-card-editor")}static getStubConfig(t){const e=Object.values(t.entities||{}).find(t=>"scanner_state"===t.translation_key&&"brother_scanner"===t.platform);return{entity:e?.entity_id||""}}setConfig(t){if(!t||!t.entity)throw new Error("Pick the scanner state sensor (entity)");this.config={show_image:!0,show_buttons:!0,show_selects:!1,show_last_scan:!0,show_link:!0,compact:!1,...t}}getCardSize(){return this.config?.compact?3:5}connectedCallback(){super.connectedCallback(),this.ticker=window.setInterval(()=>this.now=Date.now(),1e3)}disconnectedCallback(){super.disconnectedCallback(),this.ticker&&window.clearInterval(this.ticker)}get stateObj(){return this.hass?.states[this.config.entity]}get entities(){return function(t,e){const s={state:e,buttons:{},selects:{}},i=t.entities||{},n=i[e];if(!n||!n.device_id)return function(t,e,s){const i=e.replace(/^sensor\./,"").replace(/_state$/,""),n=t.states;n[`sensor.${i}_last_scan`]&&(s.lastScan=`sensor.${i}_last_scan`),n[`sensor.${i}_ocr_queue`]&&(s.ocrQueue=`sensor.${i}_ocr_queue`),n[`button.${i}_scan_rear_pages`]&&(s.rear=`button.${i}_scan_rear_pages`);for(const t of["resolution","mode","source"])n[`select.${i}_${t}`]&&(s.selects[t]=`select.${i}_${t}`);const o=n[e]?.attributes.actions||[];for(const t of o){const e=`button.${i}_${t.label.toLowerCase().replace(/[^a-z0-9]+/g,"_").replace(/^_|_$/g,"")}`;n[e]&&(s.buttons[t.target]=e)}return s}(t,e,s);for(const t of Object.values(i)){if(t.device_id!==n.device_id||t.hidden)continue;const e=t.translation_key||"",i=t.entity_id;"last_scan"===e?s.lastScan=i:"ocr_queue"===e?s.ocrQueue=i:"scan_rear"===e?s.rear=i:e.startsWith("scan_")&&i.startsWith("button.")?s.buttons[e.slice(5)]=i:["resolution","mode","source"].includes(e)&&i.startsWith("select.")&&(s.selects[e]=i)}return s}(this.hass,this.config.entity)}render(){if(!this.hass||!this.config)return V;const t=this.stateObj;if(!t)return q`<ha-card><div class="warning">Entity ${this.config.entity} not found</div></ha-card>`;const e=t.attributes,s=t.state,i=this.entities,n=this.config.name||e.friendly_name?.replace(/ State$/,"")||"Scanner",o=this.config.image||e.image_url,r=!1!==this.config.show_image&&!!o,a=e.queue||{};return q`
      <ha-card class=${this.config.compact?"compact":""}>
        <div class="header">
          ${r?q`<img class="image" src=${o} alt="" />`:V}
          <div class="title">
            <div class="name">${n}</div>
            <div class="state ${s}">
              <ha-icon icon=${gt[s]||gt.unknown}></ha-icon>
              <span>${this.stateLabel(t)}</span>
            </div>
            ${this.renderDetail(s,e,a)}
          </div>
        </div>
        ${!1!==this.config.show_buttons?this.renderButtons(s,e,i):V}
        ${this.config.show_selects?this.renderSelects(i):V}
        ${!1!==this.config.show_last_scan?this.renderLastScan(i):V}
        ${this.error?q`<div class="error">${this.error}</div>`:V}
        ${!1!==this.config.show_link&&e.web_ui_url?q`<div class="footer"><a href=${e.web_ui_url} target="_blank" rel="noopener"><ha-icon icon="mdi:open-in-new"></ha-icon> Web UI</a></div>`:V}
      </ha-card>
    `}stateLabel(t){if(this.hass.formatEntityState&&!["unavailable","unknown"].includes(t.state)){const e=this.hass.formatEntityState(t);if(e&&e!==t.state)return e}return mt[t.state]||t.state}renderDetail(t,e,s){const i=[];if("waiting_for_rear"===t&&e.waiting_until){const t=Math.max(0,Math.round((new Date(e.waiting_until).getTime()-this.now)/1e3));i.push(q`<span class="chip timer"><ha-icon icon="mdi:timer-outline"></ha-icon> ${t}s</span>`)}return"scanning"===t&&e.pages&&i.push(q`<span class="chip">${e.pages} page${1===e.pages?"":"s"}</span>`),(s.pending>0||s.in_progress>0)&&i.push(q`<span class="chip"><ha-icon icon="mdi:tray-full"></ha-icon> OCR queue ${s.pending+(s.in_progress||0)}</span>`),s.failed>0&&i.push(q`<span class="chip problem"><ha-icon icon="mdi:alert-circle-outline"></ha-icon> ${s.failed} OCR failed</span>`),!1===e.reachable&&"unreachable"!==t&&i.push(q`<span class="chip problem"><ha-icon icon="mdi:lan-disconnect"></ha-icon> device offline</span>`),i.length?q`<div class="detail">${i}</div>`:V}renderButtons(t,e,s){const i=(e.actions||[]).filter(t=>t.enabled),n=this.config.buttons,o=i.filter(t=>s.buttons[t.target]&&(!n||n.includes(t.target))),r="waiting_for_rear"===t,a=["unavailable","unknown"].includes(t)||"scanning"===t||"converting"===t;return q`
      <div class="buttons">
        ${o.map(t=>{const e=s.buttons[t.target],i=this.hass.states[e]?.state,n="email"===t.target;return q`
            <button
              class="action ${n&&r?"highlight":""}"
              ?disabled=${a||"unavailable"===i||null!==this.busy}
              @click=${()=>this.press(e,t.target)}
              title=${t.label}
            >
              <ha-icon icon=${this.busy===t.target?"mdi:loading":_t[t.target]||"mdi:scanner"} class=${this.busy===t.target?"spin":""}></ha-icon>
              <span>${t.label}</span>
            </button>
          `})}
        ${r&&s.rear&&!o.some(t=>"email"===t.target)?q`<button class="action highlight" ?disabled=${null!==this.busy} @click=${()=>this.press(s.rear,"rear")}>
              <ha-icon icon="mdi:book-open-page-variant"></ha-icon><span>Scan rear pages</span>
            </button>`:V}
      </div>
    `}renderSelects(t){const e=Object.entries(t.selects);return e.length?q`
      <div class="selects">
        ${e.map(([t,e])=>{const s=this.hass.states[e];if(!s)return V;const i=s.attributes.options||[];return q`<label class="select">
            <span>${t}</span>
            <select @change=${t=>this.select(e,t.target.value)}>
              ${i.map(t=>q`<option value=${t} ?selected=${t===s.state}>${"default"===t?"Container default":t}</option>`)}
            </select>
          </label>`})}
      </div>
    `:V}renderLastScan(t){if(!t.lastScan)return V;const e=this.hass.states[t.lastScan];if(!e||["unavailable","unknown",""].includes(e.state))return q`<div class="last-scan empty"><ha-icon icon="mdi:file-outline"></ha-icon><span>No scans yet</span></div>`;const s=e.attributes;return q`
      <div class="last-scan">
        <ha-icon icon="mdi:file-pdf-box"></ha-icon>
        <div class="file">
          <div class="file-name" title=${e.state}>${e.state}</div>
          <div class="file-meta">${this.formatSize(s.size)}${s.modified?` · ${this.formatTime(s.modified)}`:""}</div>
        </div>
        ${s.download_url?q`<button class="icon" title="Download" @click=${()=>this.download(s.download_url)}><ha-icon icon="mdi:download"></ha-icon></button>`:V}
        ${s.ocr_download_url?q`<button class="icon" title="Download OCR copy" @click=${()=>this.download(s.ocr_download_url)}><ha-icon icon="mdi:text-recognition"></ha-icon></button>`:V}
      </div>
    `}async press(t,e){this.busy=e,this.error=null;try{await this.hass.callService("button","press",{entity_id:t})}catch(t){this.error=t?.message||String(t)}finally{window.setTimeout(()=>this.busy=null,1500)}}async select(t,e){this.error=null;try{await this.hass.callService("select","select_option",{entity_id:t,option:e})}catch(t){this.error=t?.message||String(t)}}async download(t){this.error=null;try{const e=await this.hass.callWS({type:"auth/sign_path",path:t,expires:60}),s=this.hass.hassUrl?this.hass.hassUrl(e.path):e.path;window.open(s,"_blank","noopener")}catch(t){this.error=`Download failed: ${t?.message||t}`}}formatSize(t){return t||0===t?t<1024?`${t} B`:t<1048576?`${(t/1024).toFixed(0)} kB`:`${(t/1024/1024).toFixed(1)} MB`:""}formatTime(t){const e=new Date(t);if(Number.isNaN(e.getTime()))return"";const s=this.hass.locale?.language||this.hass.language||void 0;return e.toLocaleString(s,{dateStyle:"medium",timeStyle:"short"})}}$t.styles=r`
    ha-card {
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .header {
      display: flex;
      gap: 16px;
      align-items: center;
    }
    .image {
      width: 112px;
      height: 84px;
      object-fit: contain;
      flex-shrink: 0;
      border-radius: 8px;
      background: var(--secondary-background-color, #f3f4f6);
    }
    .compact .image {
      width: 72px;
      height: 54px;
    }
    .title {
      min-width: 0;
      flex: 1;
    }
    .name {
      font-size: 1.25rem;
      font-weight: 500;
      color: var(--primary-text-color);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .state {
      display: flex;
      align-items: center;
      gap: 6px;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }
    .state ha-icon {
      --mdc-icon-size: 22px;
    }
    .state.idle ha-icon {
      color: var(--success-color, #2e7d32);
    }
    .state.scanning ha-icon,
    .state.converting ha-icon,
    .state.ocr ha-icon {
      color: var(--info-color, #0288d1);
    }
    .state.waiting_for_rear ha-icon {
      color: var(--warning-color, #f9a825);
    }
    .state.unreachable ha-icon,
    .state.unavailable ha-icon {
      color: var(--error-color, #c62828);
    }
    .detail {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 0.8rem;
      padding: 2px 8px;
      border-radius: 12px;
      background: var(--secondary-background-color, #f3f4f6);
      color: var(--secondary-text-color);
    }
    .chip ha-icon {
      --mdc-icon-size: 16px;
    }
    .chip.problem {
      background: rgba(198, 40, 40, 0.12);
      color: var(--error-color, #c62828);
    }
    .chip.timer {
      font-variant-numeric: tabular-nums;
    }
    .buttons {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 8px;
    }
    button.action {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 10px 12px;
      border-radius: 8px;
      border: 1px solid var(--divider-color, #ddd);
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color);
      font: inherit;
      cursor: pointer;
      min-height: 44px;
    }
    button.action:hover:not(:disabled) {
      border-color: var(--primary-color);
      color: var(--primary-color);
    }
    button.action:disabled {
      opacity: 0.5;
      cursor: default;
    }
    button.action.highlight {
      border-color: var(--warning-color, #f9a825);
      background: rgba(249, 168, 37, 0.12);
    }
    .spin {
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }
    .selects {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 8px;
    }
    .select {
      display: flex;
      flex-direction: column;
      gap: 2px;
      font-size: 0.8rem;
      color: var(--secondary-text-color);
      text-transform: capitalize;
    }
    .select select {
      font: inherit;
      padding: 6px;
      border-radius: 6px;
      border: 1px solid var(--divider-color, #ddd);
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color);
    }
    .last-scan {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 10px;
      border-radius: 8px;
      background: var(--secondary-background-color, #f3f4f6);
    }
    .last-scan.empty {
      color: var(--secondary-text-color);
    }
    .last-scan > ha-icon {
      color: var(--error-color, #c62828);
      --mdc-icon-size: 28px;
    }
    .file {
      flex: 1;
      min-width: 0;
    }
    .file-name {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .file-meta {
      font-size: 0.8rem;
      color: var(--secondary-text-color);
    }
    button.icon {
      border: none;
      background: transparent;
      color: var(--primary-color);
      cursor: pointer;
      padding: 6px;
      border-radius: 50%;
    }
    button.icon:hover {
      background: rgba(0, 0, 0, 0.06);
    }
    .footer {
      display: flex;
      justify-content: flex-end;
      font-size: 0.85rem;
    }
    .footer a {
      color: var(--primary-color);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .footer ha-icon {
      --mdc-icon-size: 16px;
    }
    .error,
    .warning {
      color: var(--error-color, #c62828);
      font-size: 0.85rem;
    }
  `,t([dt({attribute:!1})],$t.prototype,"hass",void 0),t([pt()],$t.prototype,"config",void 0),t([pt()],$t.prototype,"busy",void 0),t([pt()],$t.prototype,"error",void 0),t([pt()],$t.prototype,"now",void 0),customElements.define("brother-scanner-card",$t),window.customCards=window.customCards||[],window.customCards.push({type:"brother-scanner-card",name:"Brother Scanner Card",description:"Scan buttons, status and the last scan of a BrotherScannerDocker container",preview:!0,documentationURL:"https://github.com/PhilippMundhenk/brother-scanner-card"}),console.info("%c BROTHER-SCANNER-CARD %c 1.0.0 ","color: white; background: #0ea5e9; font-weight: 700;","color: #0ea5e9; background: white; font-weight: 700;");export{$t as BrotherScannerCard};
