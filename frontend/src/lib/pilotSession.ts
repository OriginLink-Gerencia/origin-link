import { useEffect, useState } from "react";
import type { NavigateFunction } from "react-router-dom";
import { KEY, type Data, type Role, type Supplier } from "./demo";
import { accept, applyScoped, authenticate, demoSuppliers, initialStore, invitation, links, loadStore, register, scoped, STORE, type Identity, type Store } from "./workspaces";
const SESSION = "ol.session.v2";
function currentUser(): (Identity & {expires:number}) | null {
  try {
    const u=JSON.parse(sessionStorage.getItem(SESSION) || "null");
    return u?.expires>Date.now() ? u : null;
  } catch {return null;}
}
export function usePilot(nav:NavigateFunction) {
  const [store,setStore]=useState(loadStore), [user,setUser]=useState(currentUser), [notice,setNotice]=useState("");
  useEffect(()=>{
    function sync(e:StorageEvent){if(e.key===STORE){setStore(loadStore());}}
    window.addEventListener("storage",sync);
    return ()=>window.removeEventListener("storage",sync);
  },[]);
  useEffect(()=>{
    if(!user)return;
    const timer=window.setTimeout(()=>{sessionStorage.removeItem(SESSION);setUser(null);setNotice("La sesión ha vencido.");},Math.max(0,user.expires-Date.now()));
    return ()=>window.clearTimeout(timer);
  },[user]);
  function commit(next:Store) {localStorage.setItem(STORE,JSON.stringify(next));setStore(next);}
  function begin(u:Identity) {
    const session={role:u.role,id:u.id,expires:Date.now()+8*3600000};
    sessionStorage.setItem(SESSION,JSON.stringify(session));setUser(session);setNotice("");nav("/");
  }
  function logout(){sessionStorage.removeItem(SESSION);setUser(null);setNotice("");nav("/");}
  function update(change:(d:Data)=>Data,message:string) {
    try {
      if(!user || !currentUser())throw Error("Vuelve a iniciar sesión.");
      commit(applyScoped(loadStore(),user,change));setNotice(message);return true;
    } catch(e){setNotice((e as Error).message);return false;}
  }
  const demos=demoSuppliers(store);
  const space=store.spaces.find(s=>s.id===user?.id && user.role==="tostadora");
  function saveSupplier(entry:Supplier){
    const source=loadStore();
    const identity=entry.email && source.spaces.flatMap(s=>s.suppliers).find(p=>p.email?.toLowerCase()===entry.email?.toLowerCase());
    return update(d=>{
      const id=entry.id || (identity && identity.id) || Date.now();
      if(!entry.id && d.suppliers.some(p=>p.id===id)) throw Error("El proveedor ya está en tu directorio.");
      const saved={...entry,id};
      return {...d,suppliers:entry.id?d.suppliers.map(p=>p.id===id?saved:p):[...d.suppliers,saved]};
    },"Proveedor guardado.");
  }
  const relations=user?.role==="cooperativa"?links(store,user.id):[];
  return {data:scoped(store,user),role:user?.role??null,supplier:user?.id??0,name:space?.name ?? relations[0]?.entry.name ?? "",region:space?.region??"",notice,update,logout,saveSupplier,relations,
    demoRoasters:store.spaces.filter(s=>s.demo).map(({id,name})=>({id,name})),demoSuppliers:demos,
    login:(role:Role,id:number)=>{if(role==="tostadora"?store.spaces.some(s=>s.id===id&&s.demo):demos.some(s=>s.id===id))begin({role,id});},
    invited:(token:string)=>{try{const {space,entry}=invitation(store,token);return {name:space.name,supplier:entry.name,email:entry.email??""};}catch{return null;}},
    async credentials(email:string,password:string,name?:string,token?:string) {
      const raw=localStorage.getItem(STORE),source=loadStore();
      const result=name!==undefined?await register(source,name,email,password,token):{user:await authenticate(source,email,password),store:source};
      if(raw!==localStorage.getItem(STORE))throw Error("Los datos cambiaron en otra pestaña. Vuelve a intentarlo.");
      let next=result.store;
      if(token && name===undefined){
        const {entry}=invitation(next,token);
        if(result.user.role!=="cooperativa" || (entry.email && entry.email.toLowerCase()!==email.trim().toLowerCase()))throw Error("Usa la cuenta del proveedor invitado.");
        next=accept(next,token,result.user.id);
      }
      if(next!==source)commit(next);
      begin(result.user);
    },
    acceptLink:(token:string)=>{try{const source=loadStore(),{entry}=invitation(source,token);if(!user || user.role!=="cooperativa" || entry.id!==user.id)throw Error("Invitación no válida");commit(accept(source,token,user.id));setNotice("Vínculo aceptado.");}catch(e){setNotice((e as Error).message);}},
    reset:()=>{commit(initialStore());localStorage.removeItem(KEY);logout();setNotice("Demo restablecida.");}
  };
}
