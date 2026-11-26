import {useEffect,useState} from "react";
import {useLocation,Link} from "react-router-dom";
import {Brand,Header,ThemeButton} from "../components/UI";
import {useDemo} from "../lib/session";
import LanguageButton from "../components/LanguageButton";
import {translate} from "../lib/i18n";
import {values} from "../lib/form";
import {DEMO_EMAILS,DEMO_PASSWORD} from "../lib/pilotSession";
import {request} from "../lib/http";
type Invite={tostador:string;proveedor:string;vigente:boolean};
export default function Access() {
  const s=useDemo(),loc=useLocation(),invited=loc.pathname==="/invitacion",token=new URLSearchParams(loc.search).get("token")??"";
  const [invite,setInvite]=useState<Invite|null|undefined>(invited?undefined:null);
  const [signup,setSignup]=useState(invited),[error,setError]=useState(""),[busy,setBusy]=useState(false);
  useEffect(()=>{
    if(!invited)return;
    request<Invite>("/invitaciones/"+encodeURIComponent(token),{auth:false}).then(i=>setInvite(i.vigente?i:null)).catch(()=>setInvite(null));
  },[invited,token]);
  async function enter(email:string,password:string,name?:string,person?:string){
    setError("");setBusy(true);
    try{await s.credentials(email,password,name,invited?token:undefined,person);}catch(ex){setError((ex as Error).message);}finally{setBusy(false);}
  }
  return <><header className="top"><Brand/><span className="demo">{translate("Piloto")}</span><LanguageButton/><ThemeButton/></header>
    <main className="login" tabIndex={-1}><section className="login-form">
      <Header eyebrow={translate(invited?"Invitación privada":"Acceso a OriginLink")} title={translate(invited?"Vincular mi cooperativa":signup?"Registrar tostadora":"Entra a tu espacio")}>{invite && invite.tostador+" invita a "+invite.proveedor+" a compartir su catálogo."}</Header>
      {invited && invite===undefined ? <p role="status">Verificando la invitación…</p> : invited && !invite ? <><p role="alert">Invitación no válida o vencida. Pide una nueva a la tostadora.</p><Link to="/">Volver al inicio</Link></> : <>
      {invited && s.role==="cooperativa" && <p><button disabled={busy} onClick={async()=>{if(await s.acceptLink(token))window.location.assign("/");}}>Aceptar invitación con mi cuenta actual</button></p>}
      <form key={String(signup)+token} onSubmit={e=>{e.preventDefault();const v=values(e.currentTarget);void enter(v.email,v.password,signup?v.name:undefined,signup?v.person:undefined);}}>
        {signup && <label>Nombre de la organización<input name="name" defaultValue={invite?.proveedor} required minLength={2} autoComplete="organization"/></label>}
        {signup && <label>Tu nombre<input name="person" required minLength={2} autoComplete="name"/></label>}
        <label>Correo electrónico<input type="email" name="email" required autoComplete="username"/></label>
        <label>Contraseña<input type="password" name="password" autoComplete={signup?"new-password":"current-password"} minLength={signup?8:undefined} required/></label>
        {signup && <small>Mínimo 8 caracteres.</small>}
        {error && <p role="alert">{error}</p>}
        <button disabled={busy}>{busy?"Procesando…":signup?(invited?"Crear cuenta y aceptar":"Crear cuenta"):(invited?"Entrar y aceptar":"Iniciar sesión")}</button>
      </form>
      <button className="quiet" onClick={()=>{setSignup(!signup);setError("");}}>{signup?"Ya tengo una cuenta":invited?"Crear cuenta de cooperativa":"Registrar una tostadora"}</button></>}
      {!invited && <details className="demo-access"><summary>Probar con datos de demostración</summary>
        <p>Cuentas creadas con <code>python -m app.seed_demo</code> en el servidor.</p>
        <button disabled={busy} onClick={()=>void enter(DEMO_EMAILS.tostadora,DEMO_PASSWORD)}>Entrar como tostadora →</button>
        <button disabled={busy} className="secondary" onClick={()=>void enter(DEMO_EMAILS.cooperativa,DEMO_PASSWORD)}>Entrar como cooperativa</button>
      </details>}<p role="status">{s.notice}</p>
    </section><aside className="login-art"><img alt="" src="/identidad/07-monocromo-blanco.svg"/><h2>Tu abastecimiento,<br/>en orden.</h2><p>Del lote de origen a la próxima jornada de tueste.</p></aside></main></>;
}
