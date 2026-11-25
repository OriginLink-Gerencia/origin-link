import model from "./pilot-model.json";
import type {Week} from "./demo";
const percent = (n:number)=>n.toLocaleString("es-PE",{maximumFractionDigits:2})+" %";
function multiply(input:number[],matrix:number[][]) {
  return matrix[0].map((_,column)=>input.reduce((sum,value,row)=>sum+value*matrix[row][column],0));
}
function infer(values:number[], first:string, org:number, scale:{mean:number;std:number}) {
  const x=values.slice(-8).map(v=>(v-scale.mean)/scale.std);
  const activations=[0,2,4].flatMap(d=>multiply(x.slice(5-d,8-d),model.w1).map(Math.tanh));
  const hidden=multiply(activations,model.w2).map(Math.tanh);
  const angle=new Date(first+"T12:00:00Z").getUTCMonth()*Math.PI/6;
  const features=[...hidden,Math.sin(angle),Math.cos(angle),...[1,2,3,4].map(n=>Number(n===org)),1];
  return multiply(features,model.head).map(y=>Math.max(0,y*scale.std+scale.mean));
}
export function projection(history:Week[],org:number|undefined,first:string) {
  const last=history.slice(-4),mean=last.reduce((s,w)=>s+w.kg,0)/(last.length||1);
  const metrics=model.organizations[String(org) as keyof typeof model.organizations];
  const recent=history.slice(-8),week=7*86400000;
  const consecutive=recent.length===8 && recent.every((v,i)=>i===0||Date.parse(v.date)-Date.parse(recent[i-1].date)===week);
  const gap=recent.length?(Date.parse(first)-Date.parse(recent[recent.length-1].date))/week:Infinity;
  let method="Promedio móvil",reason="",values=Array<number>(4).fill(mean);
  if(!history.length)reason="Registra o importa consumo para obtener un pronóstico.";
  else if(!consecutive || gap<1 || gap>2)reason="El historial reciente es insuficiente para aplicar la TCN.";
  else if(!metrics || !org)reason="Esta organización aún no tiene una TCN validada.";
  else if(metrics.validation.tcn>=metrics.validation.pm4)reason="El promedio móvil tuvo menor error de validación para esta tostadora.";
  else {
    const inputs=recent.map(w=>w.kg);
    if(gap===2){
      const bridge=new Date(Date.parse(first)-week).toISOString().slice(0,10);
      inputs.push(infer(inputs,bridge,org,metrics)[0]);
    }
    values=infer(inputs,first,org,metrics);
    method="TCN global";reason="La TCN tuvo menor error de validación para esta tostadora.";
  }
  return {method,reason,values:values.map(n=>Math.round(n*100)/100),report:metrics?{validation:[metrics.validation.tcn,metrics.validation.pm4].map(percent),test:[metrics.test.tcn,metrics.test.pm4].map(percent)}:null};
}
