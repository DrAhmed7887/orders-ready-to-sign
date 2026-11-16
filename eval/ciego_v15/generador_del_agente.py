import random, csv, re, collections
rng = random.Random(1515)
S = "/private/tmp/claude-501/-Users-ahmedzayed--claude-spares-spare-SMru0l/a73ff8a4-1ba6-4cf1-b46a-61db5b5cffab/scratchpad/"
def f(a,b,d=1):
    return f"{rng.uniform(a,b):.{d}f}".replace(".",",")
FILL = [
 lambda: f"creatinina {f(0.6,2.4)} mg/dl", lambda: f"urea {rng.randint(25,90)} mg/dl",
 lambda: f"Hb {f(9,15)} g/dl", lambda: f"potasio {f(3.6,5.4)} mEq/l", lambda: f"sodio {rng.randint(133,145)} mmol/l",
 lambda: f"PCR {rng.randint(2,40)} mg/l", lambda: f"GGT {rng.randint(18,120)} U/l",
 lambda: f"NT-proBNP {rng.randint(90,1800)} pg/ml", lambda: f"ferritina {rng.randint(30,400)} ng/ml",
 lambda: f"leucocitos {rng.randint(4,12)}.{rng.randint(0,9)}00/µl", lambda: f"hematíes {rng.randint(2,25)}/campo en el sedimento",
 lambda: f"TA {rng.randint(110,160)}/{rng.randint(65,95)} mmHg", lambda: f"peso {rng.randint(55,110)} kg",
 lambda: f"HbA1c {f(5.8,9.5)} %", lambda: f"glucosa {rng.randint(90,220)} mg/dl", lambda: f"colesterol LDL {rng.randint(70,160)} mg/dl",
 lambda: f"calcio {f(8.6,10.2)} mg/dl", lambda: f"fósforo {f(2.8,5.2)} mg/dl", lambda: f"ácido úrico {f(4,9)} mg/dl",
 lambda: f"TSH {f(0.6,4.5)} mUI/l", lambda: f"plaquetas {rng.randint(150,320)}.000/µl", lambda: f"bicarbonato {rng.randint(18,27)} mmol/l",
 lambda: "proteinuria 300 mg/24 h", lambda: f"IMC {f(22,35)} kg/m2", lambda: f"bilirrubina {f(0.3,1.2)} mg/dl",
]
SAFE = [x for i,x in enumerate(FILL)]
INTRO = ["Analítica: ","En la analítica se objetivó ","Los resultados de laboratorio mostraron ","Al ingreso presentaba ",
 "En el control destacaban ","Laboratorio: ","Datos analíticos: ","En la revisión se registró ","Paciente con "]
def join(items):
    if rng.random()<0.4 and len(items)>1:
        return ", ".join(items[:-1])+" y "+items[-1]
    return ", ".join(items)
def wrap(target, extras=(), hard=False, short=False, nf=None):
    if short:
        fl=[rng.choice(FILL)() for _ in range(rng.randint(0,1))]
        items=fl+[target]+list(extras); rng.shuffle(items)
        s=rng.choice(["Se registró ","Destacaba ","En la consulta: ","Resultado: "])+join(items)
    else:
        n=nf or rng.randint(3,6)
        fl=[g() for g in rng.sample(FILL,n)]
        if hard:
            pre=fl[:2]; post=fl[2:]
            mid=[target]+list(extras)+[fl.pop() if len(fl)>3 else rng.choice(FILL)()]
            post=fl[2:]
            rng.shuffle(mid)
            s=rng.choice(INTRO)+", ".join(pre)+" ("+"; ".join(mid)+")"+("; "+", ".join(post) if post else "")
        else:
            items=fl+list(extras); items.insert(rng.randint(0,len(items)),target)
            s=rng.choice(INTRO)+join(items)
    if rng.random()<0.1: s+=f" ({rng.randint(1,28):02d}/{rng.randint(1,12):02d}/{rng.randint(2019,2025)})"
    return s+"."
rows=[]
def add(test,target,expect,value,unit,why,extras=(),hard=None,short=False):
    h = (len(rows)%3==0) if hard is None else hard
    rows.append([test,wrap(target,extras,h and not short,short),expect,value,unit,why])

# CAC value
names=["cociente albúmina/creatinina {v} {u}","cociente albumina/creatinina de {v} {u}","CAC {v} {u}","índice albúmina/creatinina {v} {u}",
 "ratio albúmina/creatinina {v} {u}","relación albúmina/creatinina {v} {u}","cociente microalbúmina/creatinina {v} {u}",
 "microalbuminuria de {v} {u}","albuminuria {v} {u}","CAC de {v} {u}","cociente albúmina/creatinina en orina de {v} {u}"]
forced={"microalbuminuria de {v} {u}","albuminuria {v} {u}"}
V={"mg/g":[8,12,18,22,28,45,60,85,120,250,340,560,4,16,29,31,95,410,7,150,34,72,5,"14,5","8,2","26,7","132,4","52,8","3,9","180","23"],
 "mg/mmol":["0,8","1,5","2,6","3","10","25","3,4","7,5"],"µg/mg":[20,45,150,"9,5",80]}
vals={k:rng.sample(v,len(v)) for k,v in V.items()}
def pick(u):
    if not vals[u]: vals[u]=rng.sample(V[u],len(V[u]))
    return str(vals[u].pop())
gen=[]
for i in range(42):
    t=names[i%len(names)]
    if t in forced: w,u="mg/g","mg/g"
    elif i%7==3: w=u="mg/mmol"
    elif i%7==5: w=u="µg/mg"
    elif i%9==4: w,u="mg/g de creatinina","mg/g"
    elif i%9==7: w,u="mg/g Cr","mg/g"
    else: w=u="mg/g"
    v=pick(u)
    gen.append((t.format(v=v,u=w),v,u))
hand=[("CAC 15 mg/g y microalbuminuria 40 mg/l","15","mg/g"),("cociente albúmina/creatinina 70 mg/g y albuminuria 8 mg/dl","70","mg/g"),
      ("CAC 22 mg/g (microalbuminuria 35 mg/l)","22","mg/g")]
allv=gen+hand
rng.shuffle(allv)
cpc=["CPC 0,15 g/g","cociente proteína/creatinina 0,2 g/g","CPC 0,35 g/g","cociente proteína/creatinina 0,12 g/g"]
for i,(t,v,u) in enumerate(allv):
    short = i<15
    ex=()
    if not short and i%5==0: ex=(rng.choice(cpc),)
    elif not short and i%5==1: ex=("orina de 24 h con proteinuria 300 mg/24 h" if rng.random()<.5 else "orina de 24 h sin hallazgos",)
    add("CAC",t,"value",v,u,"single ACR with unit"+(" (other lab nearby)" if ex else ""),ex,short=short)
# normal
norm=["microalbuminuria negativa","cociente albúmina/creatinina normal","CAC normal","albuminuria ausente","sin microalbuminuria",
 "cociente albumina/creatinina dentro de la normalidad","microalbuminuria no detectable","CAC negativo","ausencia de albuminuria",
 "índice albúmina/creatinina normal","ratio albúmina/creatinina normal","relación albúmina/creatinina sin alteraciones","microalbuminuria ausente","cociente microalbúmina/creatinina negativo","CAC dentro de rango normal"]
for t in norm: add("CAC",t,"normal","","","ACR stated normal or absent, no number")
# unreadable
unr=[("cociente albúmina/creatinina de 3,5","no unit"),("CAC 45","no unit"),("índice albúmina/creatinina 22","no unit"),("ratio albúmina/creatinina 180","no unit"),
 ("cociente albumina/creatinina 12,4","no unit"),("CAC de 67","no unit"),("relación albúmina/creatinina 300","no unit"),("microalbuminuria 35","no unit"),
 ("CAC 25 mg/g y en la repetición 80 mg/g","two ACR results"),("cociente albúmina/creatinina 40 mg/g (previo 120 mg/g)","two ACR results"),
 ("CAC 18 mg/g, posteriormente 55 mg/g","two ACR results"),("cociente albúmina/creatinina 300 mg/g en 2019 y 90 mg/g actual","two ACR results"),
 ("CAC 2,5 mg/mmol y 12 mg/mmol en la segunda muestra","two ACR results"),("CAC 60 mg/g el 12/03/2021 y 150 mg/g el 05/09/2022","two ACR results"),
 ("CAC 40 mg/g, 2","stray number after ACR"),("cociente albúmina/creatinina 55 mg/g 3","stray number after ACR"),("CAC 90 mg/g, 1,5","stray number after ACR"),("ratio albúmina/creatinina 28 mg/g, 4","stray number after ACR"),
 ("CAC <30 mg/g","upper bound"),("cociente albúmina/creatinina mayor de 50 mg/g","lower bound"),("cociente albumina/creatinina inferior a 3 mg/mmol","upper bound"),
 ("CAC > 300 mg/g","lower bound"),("CAC menor de 10 mg/g","upper bound"),("índice albúmina/creatinina superior a 30","bound, no unit"),
 ("CAC 1.200 mg/g","thousands separator"),("cociente albúmina/creatinina 2.350 mg/g","thousands separator"),("albuminuria 1.050 mg/g","thousands separator"),("CAC 3.400 µg/mg","thousands separator"),
 ("CAC 35-20 mg/g","two numbers range"),("cociente albúmina/creatinina entre 30 y 300 mg/g","range only"),
 ("cociente albúmina/creatinina (referencia <30 mg/g)","reference range only"),("CAC (valores normales 0-30 mg/g)","reference range only"),
 ("cociente albúmina/creatinina de cuarenta mg/g","number in words"),("CAC de treinta y cinco mg/g","number in words"),("CAC doscientos mg/g","number in words")]
assert len(unr)==35
for t,w in unr: add("CAC",t,"unreadable","","",w)
# not_acr
na=[("albuminuria ++","dipstick crosses"),("albuminuria ++++","dipstick crosses"),("tira reactiva con albúmina +","dipstick"),("albuminuria +++ en tira reactiva","dipstick"),
 ("albuminuria 4,5 g/24 h","24 h albumin"),("albúmina en orina de 24 h 320 mg/24 h","24 h albumin"),("microalbuminuria 25 mg/l","concentration mg/l"),
 ("albuminuria 29,8 mg/dl","concentration mg/dl"),("proteinuria 1,2 g/24 h","24 h protein"),("cociente proteína/creatinina 0,8 g/g","protein/creatinine only"),
 ("albúmina 3,2 g/dl","serum albumin"),("albúmina sérica 2,9 g/dl","serum albumin"),("microalbuminuria 80 mg/l","concentration mg/l"),
 ("albúmina urinaria 12 mg/dl","concentration mg/dl"),("proteinuria ++ en tira reactiva","dipstick protein"),("CPC 0,45 g/g","protein/creatinine only"),
 ("proteinuria de 24 h 850 mg/24 h","24 h protein"),("albuminuria 1,8 g/l","concentration g/l"),("albúmina en orina 150 mg/l","concentration mg/l"),
 ("microalbuminuria en orina de 24 h 90 mg/24 h","24 h albumin"),("albuminuria 300 mg/24 h","24 h albumin"),("proteínas en orina ++","dipstick protein"),
 ("albúmina 4,1 g/dl","serum albumin"),("albuminuria + en tira","dipstick"),("proteinuria 0,6 g/24 h","24 h protein"),("cociente proteína/creatinina 0,3 g/g","protein/creatinine only"),
 ("albúmina en orina 45 mg/l","concentration mg/l"),("microalbuminuria 150 mg/24 h","24 h albumin"),("albuminuria +++","dipstick crosses"),
 ("albúmina sérica 3,6 g/dl","serum albumin"),("albuminuria de 24 h 2,1 g/24 h","24 h albumin"),("albuminuria 12 mg/dl en muestra aislada","concentration mg/dl"),
 ("cociente proteína/creatinina 1,5 g/g","protein/creatinine only"),("tira reactiva: albúmina ++, proteínas ++","dipstick"),("albuminuria 0,9 g/l","concentration g/l")]
assert len(na)==35
for t,w in na: add("CAC",t,"not_acr","","",w+", not an ACR")
# FGe
fv=[("FG 45 ml/min","45","ml/min"),("FGe por CKD-EPI 78 ml/min/1,73 m2","78","ml/min/1,73 m2"),("filtrado glomerular de 52","52",""),
 ("FGe 33 ml/min/1,73 m2","33","ml/min/1,73 m2"),("FG estimado 61 ml/min","61","ml/min"),("filtrado glomerular estimado (CKD-EPI) 88 ml/min/1,73 m2","88","ml/min/1,73 m2"),
 ("FGe (MDRD) 27","27",""),("FG 15 ml/min/1,73 m2","15","ml/min/1,73 m2"),("FGe 102 ml/min/1,73 m2","102","ml/min/1,73 m2"),("FG de 68","68",""),
 ("filtrado glomerular 41 ml/min","41","ml/min"),("FGe 24,5 ml/min/1,73 m2","24,5","ml/min/1,73 m2"),("FGe CKD-EPI 2021 de 57","57",""),("FG 94 ml/min","94","ml/min"),("filtrado glomerular estimado 36","36","")]
fb=["FG > 60","FGe >90 ml/min/1,73 m2","filtrado superior a 60","FG mayor de 90","FGe < 15","FG <30 ml/min","filtrado glomerular estimado >60 ml/min/1,73 m2",
 "FGe menor de 15","FG inferior a 60","FGe mayor de 60 ml/min","FG > 90","filtrado glomerular superior a 90 ml/min/1,73 m2","FGe <60","FG >90 ml/min","FGe superior a 60"]
for t,v,u in fv:
    ex=("CAC 45 mg/g",) if rng.random()<.15 else ()
    add("FGe",t,"value",v,u,"eGFR number",ex)
for t in fb: add("FGe",t,"bound","","","eGFR given only as a bound")
rng.shuffle(rows)
for r in rows: 
    s=r[1]
    assert s.endswith(".") and not re.search(r"\.\s+[A-ZÁÉÍÓÚÑ]",s) and s.count(". ")==0 or True
    assert not re.search(r"\.\s+[A-ZÁÉÍÓÚÑ]",s), s
with open(S+"ciego_v15.csv","w",encoding="utf-8",newline="") as fh:
    w=csv.writer(fh); w.writerow("id,test,sentence,expect,value,unit,why".split(","))
    for i,r in enumerate(rows,1): w.writerow([f"v15-{i:03d}"]+r)
print(len(rows)); 
for k,v in sorted(collections.Counter((r[0],r[2]) for r in rows).items()): print(k,v)
