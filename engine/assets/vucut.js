/* vucut · hàm chuyển động (GSAP), cùng luật render với seecut/luancut:
   mọi phần tử ẩn bằng CSS (opacity:0) → .set ở mốc 0 + .to ở mốc t; KHÔNG dùng .from; timeline window.__timelines.master.
   Dùng: var tl=gsap.timeline({paused:true}); window.__timelines.master=tl; VC.use(tl); VC.mix('#m1',[1.2,1.5,1.9]); ... */
(function(){
  var tl=null;
  function all(sel){return typeof sel==='string'?Array.prototype.slice.call(document.querySelectorAll(sel)):[sel];}
  // chữ gradient có bóng trong CSS filter (blur(0px) drop-shadow…): tween blur nhưng GIỮ phần bóng phía sau
  function fz(el,b){if(el.__vcf==null){var f=getComputedStyle(el).filter||'none';el.__vcf=(f==='none')?'':f.replace(/^blur\([^)]*\)\s*/,'');}
    return 'blur('+b+'px)'+(el.__vcf?' '+el.__vcf:'');}
  var VC={
    use:function(t){tl=t;return VC;},

    /* ---------- CHỮ ---------- */
    // từ sans trắng: nhoè → rõ, trồi lên 8px, 0.25 s (v5: chậm hơn 15 %)
    word:function(el,t){var a=fz(el,6),z=fz(el,0);tl.set(el,{y:8,scale:.94,filter:a},0);
      tl.to(el,{opacity:1,y:0,scale:1,filter:z,duration:.25,ease:'power3.out'},t);},
    // từ khoá có chân gradient đỏ–trắng: "đập" vào từ 1.22 → 1, nhoè 10px → 0, 0.39 s (giữ bóng)
    serif:function(el,t){var a=fz(el,10),z=fz(el,0),e=VC._e||'blur';
      if(e==='slide'){tl.set(el,{clipPath:'inset(0% 100% 0% 0%)',x:-14,filter:z},0);tl.to(el,{opacity:1,duration:.01},t);
        tl.to(el,{clipPath:'inset(0% 0% 0% 0%)',x:0,duration:.34,ease:'power3.out'},t);return;}
      if(e==='drop'){tl.set(el,{y:-54,rotation:-4,scale:1.06,filter:fz(el,4),transformOrigin:'50% 100%'},0);tl.to(el,{opacity:1,duration:.08},t);
        tl.to(el,{y:0,rotation:0,scale:1,filter:z,duration:.5,ease:'back.out(2.4)'},t);return;}
      if(e==='rise'){tl.set(el,{y:36,clipPath:'inset(0% 0% 100% 0%)',filter:z},0);tl.to(el,{opacity:1,duration:.01},t);
        tl.to(el,{y:0,clipPath:'inset(0% 0% 0% 0%)',duration:.42,ease:'expo.out'},t);return;}
      if(e==='ink'){tl.set(el,{letterSpacing:'.22em',filter:fz(el,14),scale:.96},0);tl.to(el,{opacity:1,duration:.18},t);
        tl.to(el,{letterSpacing:'0em',filter:z,scale:1,duration:.55,ease:'power3.out'},t);return;}
      tl.set(el,{scale:1.22,filter:a,transformOrigin:'50% 60%'},0);
      tl.to(el,{opacity:1,duration:.12,ease:'none'},t);
      tl.to(el,{scale:1,filter:z,duration:.39,ease:'expo.out'},t);},
    // NGÔN NGỮ DỰNG của video (theme.STYLE): kiểu từ khoá + cách vào + chuyển cảnh chính
    style:function(o){VC._e=o.entry;VC._w=o.wipe;var r=document.getElementById('root');if(r&&o.kw)r.classList.add('kw-'+o.kw);},
    _el:function(cls,inner){var e=document.querySelector('#root>.'+cls);if(!e){e=document.createElement('div');e.className='trv '+cls;e.innerHTML=inner||'';
      document.getElementById('root').appendChild(e);}return e;},
    // cụm chữ trộn: mỗi con (trừ .br) một mốc = lúc từ đó được nói
    mix:function(sel,times){var kids=all(sel+'>*').filter(function(k){return !k.classList.contains('br');});
      tl.set(sel,{opacity:1},times[0]);
      kids.forEach(function(k,i){if(times[i]==null)return;(k.classList.contains('s')?VC.serif:VC.word)(k,times[i]);});},
    // HOOK: từng chữ cái hiện như gõ máy, kèm rung nhẹ; step = giãn cách giữa chữ cái
    hook:function(sel,t,step){var el=document.querySelector(sel);
      if(!el.querySelector('.ch')){var s=el.textContent;el.textContent='';s.split('').forEach(function(c){var sp=document.createElement('span');sp.className='ch';sp.textContent=c===' '?' ':c;el.appendChild(sp);});}
      tl.set(sel,{opacity:1},t);
      el.querySelectorAll('.ch').forEach(function(c,i){tl.set(c,{y:-6,scale:1.3},0);tl.to(c,{opacity:1,y:0,scale:1,duration:.16,ease:'back.out(2)'},t+i*(step||.063));});},
    // karaoke: cả câu mờ sẵn, mỗi từ sáng trắng đúng lúc nói
    kara:function(sel,times){var ks=all(sel+' span');tl.set(sel,{opacity:1},times[0]-.05);
      ks.forEach(function(k,i){if(times[i]!=null)tl.to(k,{color:'#fff',duration:.08},times[i]);});},
    // tiêu đề trên panel: từng span một
    title:function(sel,times){all(sel+'>span').forEach(function(k,i){if(times[i]==null)return;VC.word(k,times[i]);});},

    /* ---------- ĐỒ HOẠ ---------- */
    pop:function(sel,t,from){tl.set(sel,{scale:from||.5,transformOrigin:'50% 50%'},0);
      tl.to(sel,{opacity:1,duration:.06,ease:'none'},t);tl.to(sel,{scale:1,duration:.4,ease:'back.out(2)'},t);},
    // icon bóng: xoay -14° + phóng từ 0.4, rồi lơ lửng (số vòng hữu hạn tới `until`)
    orb:function(sel,t,until){tl.set(sel,{scale:.4,rotation:-14,y:20,transformOrigin:'50% 50%'},0);
      tl.to(sel,{opacity:1,duration:.08},t);tl.to(sel,{scale:1,rotation:0,y:0,duration:.5,ease:'back.out(1.8)'},t);
      VC.bob(sel,t+.5,until);},
    bob:function(sel,t,until,amp){var n=Math.max(0,Math.floor(((until||t+1.5)-t)/.7));
      for(var i=0;i<n;i++)tl.to(sel,{y:i%2?0:-(amp||6),duration:.7,ease:'sine.inOut'},t+i*.7);},
    // vật trôi có chiều sâu (dấu ?, icon): trôi từ (dx,dy) vào chỗ, rồi lơ lửng
    float:function(sel,t,until,dx,dy){tl.set(sel,{x:dx||0,y:dy==null?40:dy,scale:.85},0);
      tl.to(sel,{opacity:1,duration:.2},t);tl.to(sel,{x:0,y:0,scale:1,duration:.7,ease:'power3.out'},t);VC.bob(sel,t+.7,until,4);},
    // thẻ số liệu: bật + thanh đỏ chạy + số đếm lên từ `from` tới `to` (định dạng 984,022)
    stat:function(sel,t,from,to,d){var el=document.querySelector(sel),n=el.querySelector('.n b'),bar=el.querySelector('.bar');
      VC.pop(sel,t,.7);if(bar){tl.set(bar,{scaleX:0},0);tl.to(bar,{scaleX:1,duration:.5,ease:'power2.out'},t+.05);}
      if(n&&to!=null){var o={v:from||0};n.textContent=Math.round(o.v).toLocaleString('vi-VN');
        tl.to(o,{v:to,duration:d||.7,ease:'power2.out',onUpdate:function(){n.textContent=Math.round(o.v).toLocaleString('vi-VN');}},t);}},
    // gạch chân vẽ dần
    uline:function(sel,t){tl.set(sel,{scaleX:0},0);tl.to(sel,{opacity:1,duration:.01},t);tl.to(sel,{scaleX:1,duration:.3,ease:'power3.out'},t);},
    out:function(sel,t,d){all(sel).forEach(function(el){tl.to(el,{opacity:0,filter:fz(el,6),duration:d||.18,ease:'power2.in'},t);});},
    cut:function(sel,t){tl.set(sel,{opacity:0},t);},        // biến mất cắt cứng

    /* ---------- PANEL (B-roll đồ hoạ toàn khung) — vào/ra CẮT CỨNG như mẫu ---------- */
    panel:function(sel,t){tl.set(sel,{opacity:0,scale:1.05},0);tl.set(sel,{opacity:1},t);tl.to(sel,{scale:1,duration:.58,ease:'expo.out'},t);},
    panelOut:function(sel,t){tl.set(sel,{opacity:0},t);},
    // panel đỏ có "chữ trượt ngang" (chữ trước mờ trôi sang phải khi chữ mới vào)
    drift:function(sel,t,d){tl.to(sel,{x:120,opacity:.18,filter:'blur(4px)',duration:d||.5,ease:'power2.in'},t);},

    /* ---------- CAMERA lên NGƯỜI NÓI (#personWrap) ---------- */
    // điểm tâm phóng = mặt (fx,fy theo khung #personWrap, 0–1) — gọi một lần
    face:function(fx,fy){VC._ff=[fx,fy];VC._fo=(fx*100)+'% '+(fy*100)+'%';gsap.set('#personWrap',{transformOrigin:VC._fo});},
    // PUNCH-IN (cắt nhảy): đổi tỉ lệ TỨC THÌ đúng âm nhấn — dùng ở đoạn quan trọng
    punch:function(t,s){tl.set('#personWrap',{scale:s||1.18},t);},
    // PUSH-IN chậm: phóng dần trong cả câu (cảm giác căng dần)
    push:function(t,s,d){tl.to('#personWrap',{scale:s||1.08,duration:d||2,ease:'sine.inOut'},t);},
    // ZOOM-SLAM: phóng nhanh có quán tính (0.25 s) — cho từ khoá "bom"
    slam:function(t,s){tl.to('#personWrap',{scale:s||1.25,duration:.29,ease:'expo.out'},t);},
    reset:function(t,d){if(!d)tl.set('#personWrap',{scale:1},t);else tl.to('#personWrap',{scale:1,duration:d,ease:'power2.inOut'},t);},
    // rung khung (impact), biên độ px
    shake:function(t,amp,d){var a=amp||6,n=6,dd=(d||.24)/n;for(var i=0;i<n;i++)tl.to('#personWrap',{x:(i%2?-1:1)*a*(1-i/n),y:(i%3-1)*a*.5*(1-i/n),duration:dd,ease:'none'},t+i*dd);
      tl.to('#personWrap',{x:0,y:0,duration:dd},t+n*dd);},

    /* ---------- CHUYỂN CẢNH ---------- */
    // chớp trắng nhanh (cắt sang panel)
    flash:function(t,a){tl.set('#vcFlash',{opacity:a||.7},t);tl.to('#vcFlash',{opacity:0,duration:.25,ease:'power2.out'},t+.02);},

    /* ---------- v4 · bố cục người nói + chuyển cảnh ---------- */
    // CHIA ĐÔI: dời người nói xuống dy, bật lớp tách nền #cutWrap (đầu nổi qua mép panel), giảm vignette; trả lại ở b
    // fl=true: đầu nổi qua mép panel (cần build/cut/*.png); mặc định: người nói dời hẳn xuống dưới mép panel, KHÔNG gì phủ lên mặt
    split:function(a,b,dy,fl){var y=dy==null?240:dy;
      tl.set('#personWrap',{y:y,x:0,scale:1},a);tl.set('.vignette',{opacity:.35},a);
      if(fl)tl.set('#cutWrap',{y:y,opacity:1,clipPath:'inset(0px 0px '+(1280-(640-y))+'px 0px)'},a);
      tl.set('#personWrap',{y:0},b);tl.set('#cutWrap',{opacity:0},b);tl.set('.vignette',{opacity:1},b);},
    // THẺ NGƯỜI NÓI bo góc (210×227 tại x480 y690) nổi trên đồ hoạ; viền #cardo
    card:function(a,b){
      tl.set('#personWrap',{transformOrigin:'0 0',scale:.42,x:433.8,y:589.2,clipPath:'inset(240px 110px 500px 110px round 60px)',zIndex:9,opacity:0},a);
      tl.to('#personWrap',{opacity:1,duration:.15},a+.05);
      tl.set('#cardo',{opacity:0,scale:.8},0);tl.to('#cardo',{opacity:1,scale:1,duration:.3,ease:'back.out(2)'},a+.05);tl.set('#cardo',{opacity:0},b);
      tl.set('#personWrap',{transformOrigin:VC._fo||'50% 38%',scale:1,x:0,y:0,clipPath:'inset(0px 0px 0px 0px round 0px)',zIndex:1,opacity:1},b);},
    // KHUNG NGƯỜI NÓI NHỎ (#pip 180×195 tại x446 y700 — trong vùng an toàn) cho mọi cảnh đồ hoạ; ảnh riêng #pipImg (render nạp cùng khung với #person)
    // → không phụ thuộc #personWrap (punch/split/reset không làm hỏng khung). Vùng cắt 500×540 quanh mặt (tâm mặt ở ~46 % chiều cao khung nhỏ).
    pip:function(a,b){var f=VC._ff||[.5,.38],W=174,s=W/500,L=Math.max(0,Math.min(220,f[0]*720-250)),T=Math.max(0,Math.min(740,f[1]*1280-250));
      gsap.set('#pipImg',{left:-L*s,top:-T*s,width:720*s,height:1280*s});
      tl.set('#pip',{opacity:0,scale:.86},a);tl.to('#pip',{opacity:1,scale:1,duration:.28,ease:'back.out(1.8)'},a+.04);tl.set('#pip',{opacity:0},b);},

    end:function(T){tl.to({}, {duration:.01},T);}
  };
  // MG: hàm chuyển động cho đồ hoạ SVG (D vẽ nét pathLength=1 · W quét ngang · P bật · G mọc từ đáy · F hiện · pulse nhịp)
  window.MG={
    D:function(s,t,d,e){tl.set(s,{strokeDasharray:1,strokeDashoffset:1},0);tl.to(s,{strokeDashoffset:0,duration:d||.6,ease:e||'power2.inOut'},t);},
    W:function(s,t,d){tl.set(s,{scaleX:0,transformOrigin:'0% 50%'},0);tl.to(s,{scaleX:1,duration:d||.6,ease:'power2.inOut'},t);},
    P:function(s,t,f){tl.set(s,{scale:f==null?0:f,opacity:0,transformOrigin:'50% 50%'},0);tl.to(s,{scale:1,opacity:1,duration:.4,ease:'back.out(2)'},t);},
    G:function(s,t){tl.set(s,{scaleY:0,transformOrigin:'50% 100%'},0);tl.to(s,{scaleY:1,duration:.5,ease:'power3.out'},t);},
    F:function(s,t,o,d){tl.set(s,{opacity:0},0);tl.to(s,{opacity:o==null?1:o,duration:d||.3},t);},
    pulse:function(s,t,u){var n=Math.floor((u-t)/.6);for(var i=0;i<n;i++)tl.to(s,{scale:i%2?1:1.35,duration:.3,transformOrigin:'50% 50%'},t+i*.6);}
  };
  window.VC=VC;
})();
