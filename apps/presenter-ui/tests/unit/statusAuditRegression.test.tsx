import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { composeLocalSnapshot } from '../../src/adapters/local/LocalPresenterReadAdapter';
import { PresenterReadModelProvider } from '../../src/app/state/PresenterReadModelProvider';
import { PresenterApp } from '../../src/app/PresenterApp';
import { ComponentDetails, Monitoring, ServiceRows } from '../../src/app/StudioReadViews';
import { BackendEvidence } from '../../src/features/service-team/BackendEvidence';
import { VisibleCloudObserver } from '../../src/domain/visibleCloudObserver';

afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.useRealTimers();});
const svc:any={service:{id:'brake-id',title:'Brake Health'}, num_instance:1, service_versions:{installed_service_version:{version:'7.0.0'}},instances:{state:'CURRENT',value:[{instance_id:0,version:'7.0.0',run_state:'failed'}]}};
const component=(version:string):any=>({type:'demo-vehicle-data-provider',installed_component:{version},pending_component:null});
const cloud=(version='1.0.0'):any=>({state:'CURRENT',observedAt:new Date().toISOString(),bindingKey:'vm:unit',value:{target:'test',source:'Aos Cloud',online:'ONLINE',lifecycle:'provisioned',installedVersion:version,pendingVersion:null,releases:[],runtimeState:'NOT_REPORTED_BY_CLOUD',dataReadiness:'NOT_REPORTED_BY_CLOUD',inventory:{unitId:'unit',systemUid:'uid',components:{state:'CURRENT',value:[component(version)]},services:{state:'CURRENT',value:[svc]},teamServiceIds:{brake:'brake-id'}}}});
const local:any={mode:'LOCAL_READ_ONLY',observedAt:new Date().toISOString(),runId:'vm',registrationComplete:true,vehicles:{test:{state:'CURRENT',process:'RUNNING',overlayExists:true,imageVersion:'Factory .33'},production:{state:'CURRENT',process:'NOT_CREATED',overlayExists:false}},images:[{selector:'33/arm64',version:'Factory .33',state:'METADATA_AVAILABLE',problems:[]}],source:{state:'SELECTED_NOT_PROBED',selectedVehicle:'test'},access:{},serviceReleases:[{releaseHandle:'brake/7.0.0',runId:'vm',team:'brake',contentProfile:'v1',version:'7.0.0',serviceId:'brake-id',submitted:true,publication:{stage:'READY'}}]};
function app(readPlatform:any, snapshot:any=local){return render(<PresenterReadModelProvider dependencies={{readPort:{read:async()=>composeLocalSnapshot(snapshot),subscribe:()=>()=>{},readPlatform}} as any}><PresenterApp/></PresenterReadModelProvider>);}

test('unknown local state is not interpreted as a missing controller',async()=>{
 const snapshot={...local,vehicles:{...local.vehicles,test:{state:'UNKNOWN',process:null,overlayExists:null}},images:[]};
 app(async()=>({state:'UNAVAILABLE',observedAt:null,value:null}),snapshot);
 expect(await screen.findByText('Controller state unavailable',{selector:'strong'})).toBeVisible();
 expect(screen.queryByRole('button',{name:'Create controller'})).toBeNull();
});

test('real retired Test response remains a valid Create state',async()=>{
 const snapshot={...local,runId:null,vehicles:{...local.vehicles,test:{state:'NOT_APPLICABLE',reason:'TARGET_NOT_CONFIGURED',process:null,imageVersion:null,overlayExists:null}}};
 app(async()=>({state:'UNAVAILABLE',observedAt:null,value:null}),snapshot);
 expect(await screen.findByRole('button',{name:'Create controller'})).toBeVisible();
 expect(screen.queryByText('Controller state unavailable',{selector:'strong'})).toBeNull();
});

test('regression: old active instance does not confirm the selected Running release',async()=>{
 const value=cloud();value.value.inventory.services.value=[{...svc,instances:{state:'CURRENT',value:[{instance_id:0,version:'6.0.0',run_state:'active'}]}}];
 const view=app(vi.fn().mockResolvedValue(value));await screen.findByTestId('studio-workspace');
 fireEvent.click(screen.getByRole('button',{name:'Brake Team'}));
 await screen.findByText('Instance 0 · 6.0.0 · active');
 expect(view.container.querySelector('.studio-release-stages > div:last-child')).not.toHaveClass('complete');
});
test('regression: open details follow refreshed inventory',async()=>{
 let value=cloud(); const read=vi.fn(async()=>value);app(read);
 await screen.findByRole('button',{name:/Vehicle Data Platform.*1.0.0/});
 fireEvent.click(screen.getByRole('button',{name:/Vehicle Data Platform.*1.0.0/}));
 expect(screen.getByRole('dialog')).toHaveTextContent('1.0.0');
 value=cloud('2.0.0');fireEvent.click(screen.getByRole('button',{name:/^Refresh$/}));
 await screen.findByRole('button',{name:/Vehicle Data Platform.*2.0.0/});
 expect(screen.getByRole('dialog')).toHaveTextContent('2.0.0');
 expect(screen.getByRole('dialog')).not.toHaveTextContent('last known');
});
test('regression: component failure reason remains visible',()=>{
 render(<ComponentDetails current row={{...component('1.0.0'),pending_component:{version:'2.0.0'},pending_component_status:'failed',pending_component_error:'CERTIFICATE_EXPIRED'} as any}/>);
 expect(screen.getByText('failed')).toBeVisible();expect(screen.getByText('CERTIFICATE_EXPIRED')).toBeVisible();
});
test('regression: service-level errors and unexpanded pending status remain visible',()=>{
 render(<ServiceRows rows={{state:'CURRENT',value:[{...svc,error_message:'IMAGE_PULL_FAILED',service_versions:{...svc.service_versions,pending_service_version_id:'new-version',pending_service_version_status:'failed'}}]}}/>);
 expect(screen.getByText(/IMAGE_PULL_FAILED/)).toBeVisible(); expect(screen.getByText(/Pending version not yet reported · failed/)).toBeVisible();
});
test('regression: backend distinguishes missing expected-version results',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({state:'OBSERVED',team:'brake',source:'REAL_BACKEND_HTTP',observedAt:new Date().toISOString(),observations:{readiness:{state:'OBSERVED',data:{ready:true}},mockData:{state:'OBSERVED',data:{source:'DEMO_MOCK',vehicleTelemetry:false,unitSystemUid:'uid',counts:[{count:1}],records:[{backendReceivedAt:new Date().toISOString(),message:{messageType:'WINDOW_COMPLETION',serviceVersion:'7.0.0',unitSystemUid:'uid',content:{status:'old-release-result'}}}]}}}})}));
 render(<BackendEvidence team='brake' unitSystemUid='uid' expectedVersion='8.0.0'/>);
 expect(await screen.findByText(/No result for release 8.0.0 yet/)).toBeVisible(); expect(screen.queryByText('old-release-result')).toBeNull();
});
test('regression: HTTP 200 section failures remain explicit',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({unitId:'unit',readCompletedAt:new Date().toISOString(),monitoring:{state:'UNKNOWN',reason:'HTTP_403',value:null}})}));
 render(<Monitoring inventory={cloud().value.inventory}/>);
 await waitFor(()=>expect(screen.queryByText(/Reading/)).toBeNull());
 expect(screen.getByRole('alert')).toHaveTextContent('HTTP_403'); expect(screen.queryByText('No sample reported for this scope.')).toBeNull();
});
test('regression: hung refresh ages the prior report to STALE',async()=>{
 vi.useFakeTimers();const read=vi.fn().mockResolvedValueOnce(cloud()).mockImplementation(()=>new Promise(()=>{}));
 const observer=new VisibleCloudObserver(read);let state:any;observer.subscribe(value=>state=value);const leave=observer.enter();await observer.refresh();
 await vi.advanceTimersByTimeAsync(44000);expect(read).toHaveBeenCalledTimes(2);expect(state.loading).toBe(true);expect(state.observation.state).toBe('STALE');expect(state.observation.reason).toBe('CLOUD_READ_SLOW');leave();
});
