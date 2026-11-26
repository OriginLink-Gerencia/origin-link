import {performance} from "../lib/performance";
import {useState} from "react";
import {Action, Header, Panel, Table} from "../components/UI";
import {dateLabel,kg,pending,received,type Supplier} from "../lib/demo";
import {values} from "../lib/form";
import {useDemo} from "../lib/session";

function DirectoryForm({entry}:{entry?:Supplier}) {
  const s=useDemo();
  return <details><summary>{entry?"Editar contacto":"Registrar proveedor"}</summary><form onSubmit={e=>{
    e.preventDefault();const form=e.currentTarget,v=values(form);
    void s.saveSupplier({...entry,id:entry?.id??0,linked:entry?.linked??false,invited:entry?.invited??false,name:v.name.trim(),region:v.region.trim(),contact:v.contact.trim(),phone:v.phone.trim(),email:v.email.trim().toLowerCase()}).then(ok=>{if(ok){form.closest("details")?.removeAttribute("open");if(!entry)form.reset();}});
  }}><div className="fields">{([["name","Nombre del proveedor"],["region","Región de origen"],["contact","Persona de contacto"],["email","Correo de contacto"],["phone","Teléfono"]] as const).map(([key,label])=><label key={key}>{label}<input name={key} defaultValue={entry?.[key]} required={key==="name"} pattern={key==="name"?".*\\S.*":undefined} type={key==="email"?"email":key==="phone"?"tel":"text"} readOnly={key==="email"&&Boolean(entry?.linked||entry?.invited)}/></label>)}</div><button>Guardar proveedor</button></form></details>;
}
function DirectoryCard({p}:{p:Supplier}) {
  const s=useDemo(), [copy,setCopy]=useState(""), active=p.invited && (p.expires??0)>Date.now();
  const url=window.location.origin+"/invitacion?token="+encodeURIComponent(p.token??"");
  const orders=s.data.orders.filter(o=>s.data.lots.find(l=>l.id===o.lot)?.supplier===p.id),stats=performance(orders);
  return <article className="network-card"><header><div><small>{p.region}</small><h3>{p.name}</h3></div><span className="tag">{p.linked?"Vinculado":active?"Invitado":"Sin vincular"}</span></header>
    {(p.contact||p.email||p.phone)&&<p>{[p.contact,p.email,p.phone].filter(Boolean).join(" · ")}</p>}
    {stats?<p>{stats.weight} de kilos recibidos · {stats.onTime} de entregas a tiempo · {stats.count} compras recibidas</p>:<p>Sin entregas completadas para calcular el cumplimiento.</p>}
    <div className="network-actions">{p.linked?<Action secondary to={"/lotes?proveedor="+p.id}>Ver lotes</Action>:!active?<button onClick={()=>void s.invite(p.id)}>Invitar proveedor</button>:null}
    <Action secondary to={"/compras?proveedor="+p.id}>Historial de compras</Action></div>
    {active&&<div className="invite-link"><label>Enlace vigente hasta el {new Date(p.expires!).toLocaleDateString("es-PE")}<input readOnly value={url} onFocus={e=>e.target.select()}/></label><button className="secondary" onClick={async()=>{try{await navigator.clipboard.writeText(url);setCopy("Enlace copiado.");}catch{setCopy("Selecciona el enlace para copiarlo.");}}}>Copiar enlace</button><span role="status">{copy}</span></div>}
    <DirectoryForm entry={p}/></article>;
}
export default function Partners(){
  const s=useDemo();
  if(s.role==="tostadora")return <><Header eyebrow={s.name} title="Proveedores">Tu directorio de abastecimiento y el cumplimiento de las entregas.</Header><section className="panel"><DirectoryForm/></section>
    <Panel title="Directorio privado">{!s.data.suppliers.length?<p>Aún no has registrado proveedores.</p>:<div className="network-list">{s.data.suppliers.map(p=><DirectoryCard key={p.id} p={p}/>)}</div>}</Panel></>;
  const active=s.relations.filter(r=>r.entry.linked),invitations=s.relations.filter(r=>!r.entry.linked);
  return <><Header eyebrow={s.name} title="Vínculos y pedidos">Consulta las tostadoras que reciben tu café y sigue sus pedidos.</Header>
    <Panel title={"Tostadoras vinculadas ("+active.length+")"}><div className="network-list">{active.map(r=><article className="network-card" key={r.id}><header><div><small>{r.region}</small><h3>{r.name}</h3></div><span className="tag">Vínculo activo</span></header><p>{s.data.orders.filter(o=>o.roaster===r.name).length} pedidos registrados</p></article>)}</div>{!active.length&&<p>Aún no tienes tostadoras vinculadas.</p>}</Panel>
    {invitations.length>0 && <Panel title="Invitaciones pendientes">{invitations.map(r=><div className="item" key={r.id}><strong>{r.name}</strong><button onClick={()=>s.acceptLink(r.entry.token!)}>Aceptar invitación</button></div>)}</Panel>}
    <Panel title="Pedidos de mis tostadoras">{!s.data.orders.length?<p>Aún no hay pedidos de tus lotes.</p>:<Table labels={["Tostadora","Lote","Compra","Entrega acordada","Acordado","Recibido","Por entregar"]}>{s.data.orders.map(o=><tr key={o.id}><td>{o.roaster}</td><td>{s.data.lots.find(l=>l.id===o.lot)?.code}</td><td>{dateLabel(o.date)}</td><td>{dateLabel(o.due)}</td><td>{kg(o.kg)}</td><td>{kg(received(o))}</td><td>{kg(pending(o))}</td></tr>)}</Table>}</Panel></>;
}
