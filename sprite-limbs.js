/* Partition each source pixel once. The old walker stamped the full two-leg
   region twice, producing extra legs. Cached masks preserve the original art. */
window.NinjaLimbs = (() => {
  const images = new WeakMap();
  function parts(image, meta, pose, hip) {
    let cache = images.get(image); if (!cache) images.set(image, cache = new Map());
    const cut = Math.round(meta.ay - hip), id = [pose.i,meta.cw,meta.ch,cut].join(':');
    if (cache.has(id)) return cache.get(id);
    const canvas=()=>{const c=document.createElement('canvas');c.width=meta.cw;c.height=meta.ch;return c;};
    const source=canvas(), ctx=source.getContext('2d',{willReadFrequently:true});
    ctx.drawImage(image,pose.i*meta.cw,0,meta.cw,meta.ch,0,0,meta.cw,meta.ch);
    const original=ctx.getImageData(0,0,meta.cw,meta.ch), left=ctx.createImageData(meta.cw,meta.ch),right=ctx.createImageData(meta.cw,meta.ch),body=ctx.createImageData(meta.cw,meta.ch);
    let seam=meta.ax;
    for(let y=0;y<meta.ch;y++){
      const runs=[];let start=-1;
      for(let x=0;x<=meta.cw;x++){
        const opaque=x<meta.cw&&original.data[(y*meta.cw+x)*4+3]>32;
        if(opaque&&start<0)start=x;
        if(!opaque&&start>=0){if(x-start>=2)runs.push([start,x]);start=-1;}
      }
      if(y===cut&&runs.length){seam=(runs[0][0]+runs[runs.length-1][1])/2;}
      if(y>=cut&&runs.length>1){
        const gaps=runs.slice(1).map((run,i)=>({x:(runs[i][1]+run[0])/2,w:run[0]-runs[i][1]}));
        gaps.sort((a,b)=>Math.abs(a.x-seam)-Math.abs(b.x-seam));
        if(gaps[0].w>0)seam=gaps[0].x;
      }
      for(let x=0;x<meta.cw;x++){
        const i=(y*meta.cw+x)*4, dst=y<cut?body:(x<seam?left:right);
        for(let channel=0;channel<4;channel++)dst.data[i+channel]=original.data[i+channel];
      }
    }
    const result={cut,hip:meta.ay-cut, source, masks:[body,left,right].map(data=>{const c=canvas();c.getContext('2d').putImageData(data,0,0);return c;})};
    cache.set(id,result);return result;
  }
  return {parts};
})();

