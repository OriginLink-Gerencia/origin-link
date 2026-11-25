import database from "../../db.json";
import { KEY, loadDemo, type Data, type Lot, type Role, type Supplier } from "./demo";

export type Identity = { role: Role; id: number };
export type Space = Omit<Data, "lots"> & {id: number; name: string; region: string; email?: string; demo?: boolean};
type Credential = Identity & {email: string; salt: string; hash: string};
export type Store = { spaces: Space[]; lots: Lot[]; accounts: Credential[] };
export const STORE = "originlink.piloto.v2";
export const DEMO_PASSWORD = "OriginLink2026!";
const empty = (): Data => ({ suppliers: [], lots: [], moves: [], orders: [], history: [] });
export function initialStore(): Store {
  const pilot = JSON.parse(JSON.stringify(database.pilot)) as Omit<Store,"accounts">;
  return {...pilot, accounts: []};
}
export function loadStore(): Store {
  const raw = localStorage.getItem(STORE);
  if (raw) return JSON.parse(raw) as Store;
  const store = initialStore();
  if (localStorage.getItem(KEY)) {
    const legacy = loadDemo();
    const {lots, ...rest} = legacy;
    store.spaces.push({...rest, id: 5, name:"Tostadora Andina · piloto anterior", region:"Lima", demo:true});
    store.lots.push(...lots);
  }
  return store;
}
export function links(store: Store, supplier: number) {
  return store.spaces.flatMap(({id,name,region,suppliers}) => {
    const entry = suppliers.find(s => s.id === supplier && (s.linked || (s.invited && (s.expires ?? 0)>Date.now())));
    return entry ? [{id,name,region,entry}] : [];
  });
}
export function scoped(store: Store, user: Identity | null): Data {
  if (!user) return empty();
  if (user.role === "tostadora") {
    const space = store.spaces.find(s => s.id === user.id);
    if (!space) return empty();
    const lots = store.lots.filter(l => l.owner ? l.owner === space.id : space.suppliers.some(s=>s.id===l.supplier && s.linked));
    return {organization:space.id,suppliers:space.suppliers, moves:space.moves, history:space.history, orders:space.orders, lots};
  }
  const relations = links(store,user.id);
  const own = relations.find(r=>r.entry.linked)?.entry ?? relations[0]?.entry;
  const lots = store.lots.filter(l => !l.owner && l.supplier === user.id);
  const orders = store.spaces.filter(s=>relations.some(r=>r.id===s.id && r.entry.linked)).flatMap(s=>
    s.orders.filter(o=>lots.some(l=>l.id===o.lot)).map(o=>({...o,roaster:s.name})));
  return {...empty(), lots, orders, suppliers:own ? [own] : []};
}
export function applyScoped(store:Store,user:Identity,change:(d:Data)=>Data):Store {
  const current=scoped(store,user), next=change(current);
  const lots = next.lots === current.lots ? store.lots : [
    ...store.lots.map(l=>next.lots.find(n=>n.id===l.id) ?? l),
    ...next.lots.filter(l=>!store.lots.some(old=>old.id===l.id))
  ];
  const spaces = store.spaces.map(s=>user.role==="tostadora" && s.id===user.id
    ? {...s, suppliers:next.suppliers,orders:next.orders,moves:next.moves,history:next.history} : s);
  return {...store,spaces,lots};
}
export function demoSuppliers(store: Store) {
  const ids = new Set(database.pilot.spaces.flatMap(s=>s.suppliers.filter(p=>p.linked).map(p=>p.id)));
  if(store.spaces.some(s=>s.id===5 && s.demo)) database.suppliers.filter(s=>s.linked).forEach(s=>ids.add(s.id));
  return [...ids].sort((a,b)=>links(store,b).length-links(store,a).length).flatMap(id=>links(store,id)[0]?.entry ?? []);
}
export function invitation(store: Store, token:string) {
  for (const space of store.spaces) {
    const entry=space.suppliers.find(s=>s.invited && s.token===token && (s.expires??0)>Date.now());
    if(entry) return {space,entry};
  }
  throw Error("Invitación no válida. Pide una nueva a la tostadora.");
}
export function createInvitation(s:Supplier) {
  if(s.linked) throw Error("El proveedor ya está vinculado.");
  return {...s, invited:true, token:crypto.randomUUID(), expires:Date.now()+7*86400000};
}
export function accept(store:Store,token:string,id:number) {
  const {space,entry}=invitation(store,token);
  if(space.suppliers.some(s=>s.id===id && s!==entry)) throw Error("Ya existe una relación con este proveedor.");
  return {...store,spaces:store.spaces.map(s=>s.id!==space.id?s:{...s,suppliers:s.suppliers.map(p=>p!==entry?p:{...p,id,linked:true,invited:false,token:undefined,expires:undefined})}),
    lots:store.lots.map(l=>l.owner===space.id && l.supplier===entry.id?{...l,supplier:id}:l)};
}
const normalize=(s:string)=>s.trim().toLowerCase();
async function digest(password:string,salt:string) {
  const enc=new TextEncoder(), key=await crypto.subtle.importKey("raw",enc.encode(password),"PBKDF2",false,["deriveBits"]);
  const bits=await crypto.subtle.deriveBits({name:"PBKDF2",salt:enc.encode(salt),iterations:100000,hash:"SHA-256"},key,256);
  return Array.from(new Uint8Array(bits),b=>b.toString(16).padStart(2,"0")).join("");
}
function seededAccount(store:Store,email:string):Identity|undefined {
  const space=store.spaces.find(s=>s.demo && s.email===email);
  if(space) return {role:"tostadora",id:space.id};
  const supplier=demoSuppliers(store).find(s=>s.email===email);
  if(supplier) return {role:"cooperativa",id:supplier.id};
}
export async function authenticate(store:Store,email:string,password:string):Promise<Identity> {
  email=normalize(email);
  const existing=store.accounts.find(a=>a.email===email);
  if(existing && await digest(password,existing.salt)===existing.hash) return {id:existing.id,role:existing.role};
  const demo=seededAccount(store,email);
  if(demo && password===DEMO_PASSWORD) return demo;
  throw Error("Correo o contraseña incorrectos");
}
export async function register(store:Store,name:string,email:string,password:string,token?:string) {
  email=normalize(email);
  if(!name.trim() || !email || password.length<8) throw Error("Completa el nombre, el correo y una contraseña de al menos 8 caracteres.");
  if(store.accounts.some(a=>a.email===email) || seededAccount(store,email)) throw Error("Ya existe una cuenta con este correo");
  const entry=token?invitation(store,token).entry:undefined;
  if(entry?.email && normalize(entry.email)!==email) throw Error("Usa el correo del proveedor invitado.");
  const user:Identity={role:entry?"cooperativa":"tostadora",id:entry?.id??Date.now()};
  let next=token?accept(store,token,user.id):{...store,spaces:[...store.spaces,{...empty(),id:user.id,name:name.trim(),region:"",email}]};
  const salt=crypto.randomUUID(),hash=await digest(password,salt);
  next={...next,accounts:[...next.accounts,{...user,email,salt,hash}]};
  return {store:next,user};
}
