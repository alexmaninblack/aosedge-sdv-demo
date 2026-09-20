import {test,expect} from '@playwright/test';
for (const viewport of [{width:1280,height:720},{width:1512,height:982},{width:1118,height:1124}]) test(`populated backend Records are paginated within ${viewport.width}x${viewport.height}`,async({page})=>{
 await page.setViewportSize(viewport);
 await page.route('**/api/**',route=>{
  const path=new URL(route.request().url()).pathname, time=new Date().toISOString();
  if(path.endsWith('/operations'))return route.fulfill({json:{sessionId:'audit',active:null,uncertain:false,jobs:[]}});
  if(path.endsWith('/snapshot'))return route.fulfill({json:{mode:'LOCAL_READ_ONLY',observedAt:time,runId:'audit',registrationComplete:true,images:[{selector:'33/arm64',version:'Factory .33',state:'METADATA_AVAILABLE',problems:[]}],access:{},vehicles:{test:{state:'CURRENT',process:'RUNNING',overlayExists:true,imageVersion:'Factory .33'},production:{state:'CURRENT',process:'NOT_CREATED',overlayExists:false}},source:{state:'CONNECTED',selectedVehicle:'test',currentVehicle:'test'}}});
  if(path.endsWith('/platform'))return route.fulfill({json:{state:'CURRENT',bindingKey:'audit:unit',observedAt:time,value:{source:'Aos Cloud',target:'test',online:'ONLINE',installedVersion:'1.0.0',releases:[],runtimeState:'NOT_REPORTED_BY_CLOUD',dataReadiness:'NOT_REPORTED_BY_CLOUD',inventory:{unitId:'unit',systemUid:'uid',components:{state:'CURRENT',value:[]},services:{state:'CURRENT',value:[]}}}}});
  if(path.endsWith('/backend/brake'))return route.fulfill({json:{team:'brake',state:'OBSERVED',source:'REAL_BACKEND_HTTP',observedAt:time,observations:{readiness:{state:'OBSERVED',data:{ready:true}},mockData:{state:'OBSERVED',data:{source:'DEMO_MOCK',vehicleTelemetry:false,unitSystemUid:'uid',counts:[{count:20}],records:Array.from({length:20},(_,n)=>({backendReceivedAt:time,message:{messageType:'RECORD_'+n,serviceVersion:'1.0.0',unitSystemUid:'uid'}}))}}}}});
  return route.abort();
 });
 await page.goto(viewport.width === 1118 ? '/#native-browser' : '/');await page.getByRole('button',{name:'Brake backend Open dashboard',exact:true}).click();
 await page.getByRole('button',{name:'Records',exact:true}).click();
 await page.getByRole('button',{name:'Show mock history'}).click();
 await page.getByRole('button',{name:'Records',exact:true}).click();await expect(page.getByRole('button',{name:/RECORD_0 /})).toBeVisible();
 await expect(page.getByRole('button',{name:/RECORD_19/})).toHaveCount(0);
 for(let n=0;n<(viewport.height <= 800 ? 19 : 9);n++) await page.getByRole('button',{name:'Next',exact:true}).click();
 await expect(page.getByRole('button',{name:/RECORD_19/})).toBeVisible();
 const layout=await page.locator('.studio-modal-layer > .modal > .modal-body').evaluate(node=>({clientHeight:node.clientHeight,scrollHeight:node.scrollHeight,overflow:getComputedStyle(node).overflowY,lastBottom:node.querySelector('.studio-inventory button:last-child')!.getBoundingClientRect().bottom,bodyBottom:node.getBoundingClientRect().bottom}));

 expect(layout.scrollHeight).toBeLessThanOrEqual(layout.clientHeight + 1); expect(layout.lastBottom).toBeLessThanOrEqual(layout.bodyBottom + 1);
 await expect(page.getByRole('button',{name:'Next',exact:true})).toBeDisabled();
});
