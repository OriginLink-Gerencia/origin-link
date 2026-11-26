"""Export a small global causal TCN for offline inference on the four pilot series.

Run with Python and NumPy from any directory. The last six weeks are test-only.
The preceding eight weeks select the epoch and the method for each organization.
"""
import csv
import json
from datetime import date
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
source = root.parent / "ml/datos_sinteticos/generados/consumo_semanal_completo.csv"
series = {}
with source.open(encoding="utf-8-sig") as stream:
    for row in csv.DictReader(stream):
        series.setdefault(int(row["tostador_id"][1:]), []).append(
            (date.fromisoformat(row["fecha"]), float(row["kg_consumidos"]))
        )

rng = np.random.default_rng(42)
w1 = rng.normal(0, 0.22, (3, 6))
w2 = rng.normal(0, 0.15, (18, 6))
head = rng.normal(0, 0.1, (13, 4))
params = [w1, w2, head]
mom = [np.zeros_like(p) for p in params]
var = [np.zeros_like(p) for p in params]
groups = {"train": [], "validation": [], "test": []}
metrics = {}
for org, rows in series.items():
    rows.sort()
    y = np.array([v for _, v in rows])
    end = len(y) - 14
    mean, std = float(y[:end].mean()), float(y[:end].std()) or 1
    metrics[org] = {"mean": mean, "std": std}
    for t in range(8, len(y) - 3):
        # All four targets must belong to the same partition.
        split = "train" if t+4 <= end else "validation" if end <= t and t+4 <= end+8 else "test" if t >= end+8 else None
        if split:
            month = (rows[t][0].month-1)*np.pi/6
            extra = [np.sin(month), np.cos(month), *[int(k == org) for k in series], 1]
            groups[split].append((org, (y[t-8:t]-mean)/std, extra, (y[t:t+4]-mean)/std))

def arrays(group):
    return [np.array([row[k] for row in group]) for k in (1, 2, 3)]

def forward(x, extra):
    # Two causal convolutions, kernel size 3, dilations 1 and 2.
    patches = np.stack([x[:, 7-d-2:8-d] for d in (0, 2, 4)], axis=1)
    a = np.tanh(patches @ w1)
    b = np.tanh(a.reshape(len(x), 18) @ w2)
    features = np.column_stack([b, extra])
    return features @ head, (patches, a, b, features)

train = arrays(groups["train"])
validation = arrays(groups["validation"])
best_loss, best, best_epoch = np.inf, None, 0
for epoch in range(1, 801):
    out, (patches, a, b, features) = forward(*train[:2])
    grad = 2*(out-train[2])/out.size
    db = (grad @ head[:6].T)*(1-b*b)
    da = (db @ w2.T).reshape(a.shape)*(1-a*a)
    grads = [patches.reshape(-1, 3).T @ da.reshape(-1, 6), a.reshape(len(a), 18).T @ db, features.T @ grad]
    for i, (param, g) in enumerate(zip(params, grads)):
        mom[i] = .9*mom[i]+.1*g
        var[i] = .999*var[i]+.001*g*g
        param -= .006*(mom[i]/(1-.9**epoch))/(np.sqrt(var[i]/(1-.999**epoch))+1e-8)
    val = np.mean((forward(*validation[:2])[0]-validation[2])**2)
    if val < best_loss:
        best_loss, best_epoch, best = val, epoch, [p.copy() for p in params]
    if epoch-best_epoch >= 65:
        break
w1, w2, head = best

for split in ("validation", "test"):
    for org, stat in metrics.items():
        x, extra, y = arrays([r for r in groups[split] if r[0] == org])
        actual = y*stat["std"]+stat["mean"]
        tcn = forward(x, extra)[0]*stat["std"]+stat["mean"]
        baseline = x[:, -4:].mean(axis=1, keepdims=True)*stat["std"]+stat["mean"]
        def mape(pred):
            usable = actual > 0
            return round(float((np.abs((actual-pred)[usable]/actual[usable])).mean()*100), 2)
        stat[split] = {"tcn": mape(tcn), "pm4": mape(baseline)}
export = {"w1": w1.tolist(), "w2": w2.tolist(), "head": head.tolist(), "organizations": metrics}
(root / "src/lib/pilot-model.json").write_text(json.dumps(export, indent=2)+"\n", encoding="utf-8")

