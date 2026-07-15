#!/usr/bin/env python3
"""One large connected workflow chart for the Lee Lab Colony DB (+ title slide)."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn

BLUE=RGBColor(0x25,0x63,0xEB); DBLUE=RGBColor(0x1E,0x3A,0x8A); GREEN=RGBColor(0x15,0x80,0x3D)
DGREEN=RGBColor(0x0F,0x5A,0x2E); AMBER=RGBColor(0xB4,0x53,0x09); PURPLE=RGBColor(0x7C,0x3A,0xED)
SLATE=RGBColor(0x33,0x41,0x55); GREY=RGBColor(0x64,0x74,0x8B); WHITE=RGBColor(0xFF,0xFF,0xFF)
INK=RGBColor(0x1A,0x1D,0x26); CONN=RGBColor(0x94,0xA3,0xB8)

prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
BLANK=prs.slide_layouts[6]; SW=prs.slide_width

def slide(): return prs.slides.add_slide(BLANK)

def textbox(sl,s,l,t,w,h,size=18,color=INK,bold=False,align=PP_ALIGN.LEFT,anchor=MSO_ANCHOR.TOP,italic=False):
    tb=sl.shapes.add_textbox(Inches(l),Inches(t),Inches(w),Inches(h)); tf=tb.text_frame
    tf.word_wrap=True; tf.vertical_anchor=anchor; p=tf.paragraphs[0]; p.alignment=align
    r=p.add_run(); r.text=s; f=r.font; f.size=Pt(size); f.bold=bold; f.italic=italic; f.color.rgb=color; f.name="Calibri"
    return tb

# box() records geometry so connectors can snap to edges
def box(sl,l,t,w,h,text,fill=BLUE,font=WHITE,size=12,bold=True,sub=None,line=None):
    shp=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(l),Inches(t),Inches(w),Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb=fill
    if line is None: shp.line.fill.background()
    else: shp.line.color.rgb=line; shp.line.width=Pt(1.25)
    shp.shadow.inherit=False
    tf=shp.text_frame; tf.word_wrap=True; tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    for m in ("margin_left","margin_right","margin_top","margin_bottom"): setattr(tf,m,Inches(0.05))
    p=tf.paragraphs[0]; p.alignment=PP_ALIGN.CENTER
    r=p.add_run(); r.text=text; r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=font; r.font.name="Calibri"
    if sub:
        p2=tf.add_paragraph(); p2.alignment=PP_ALIGN.CENTER
        r2=p2.add_run(); r2.text=sub; r2.font.size=Pt(size-2); r2.font.color.rgb=font; r2.font.name="Calibri"
    return {"l":l,"t":t,"w":w,"h":h,"shp":shp}

def R(b): return (b["l"]+b["w"], b["t"]+b["h"]/2)
def L(b): return (b["l"], b["t"]+b["h"]/2)
def T(b): return (b["l"]+b["w"]/2, b["t"])
def B(b): return (b["l"]+b["w"]/2, b["t"]+b["h"])

def connect(sl,p1,p2,color=CONN,width=1.75,two=False,dash=False):
    c=sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(p1[0]),Inches(p1[1]),Inches(p2[0]),Inches(p2[1]))
    c.line.color.rgb=color; c.line.width=Pt(width)
    ln=c.line._get_or_add_ln()
    if dash:
        d=ln.makeelement(qn('a:prstDash'),{'val':'dash'}); ln.append(d)
    te=ln.makeelement(qn('a:tailEnd'),{'type':'triangle','w':'med','len':'med'}); ln.append(te)
    if two:
        he=ln.makeelement(qn('a:headEnd'),{'type':'triangle','w':'med','len':'med'}); ln.append(he)
    return c

def note(sl,s,l,t,w,color=AMBER,size=10):
    return textbox(sl,s,l,t,w,0.3,size=size,color=color,italic=True,align=PP_ALIGN.CENTER)

# ============================================================ Slide 1: title
s=slide()
bg=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,SW,prs.slide_height); bg.fill.solid()
bg.fill.fore_color.rgb=DBLUE; bg.line.fill.background(); bg.shadow.inherit=False
textbox(s,"🐭 Lee Lab Mouse Colony Database",1,2.6,11.3,1.2,size=40,color=WHITE,bold=True,align=PP_ALIGN.CENTER)
textbox(s,"How it works, end to end — and why different users see different things",
        1,3.9,11.3,0.8,size=20,color=RGBColor(0xC7,0xD6,0xF5),align=PP_ALIGN.CENTER)

# ============================================================ Slide 2: big chart
s=slide()
bar=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,SW,Inches(0.75)); bar.fill.solid()
bar.fill.fore_color.rgb=DBLUE; bar.line.fill.background(); bar.shadow.inherit=False
tf=bar.text_frame; tf.margin_left=Inches(0.4); tf.vertical_anchor=MSO_ANCHOR.MIDDLE
r=tf.paragraphs[0].add_run(); r.text="Lee Lab Colony DB — one connected workflow"
r.font.size=Pt(22); r.font.bold=True; r.font.color.rgb=WHITE; r.font.name="Calibri"
# legend
textbox(s,"Roles:",10.15,0.22,0.8,0.32,size=11,color=RGBColor(0xC7,0xD6,0xF5),bold=True)
for i,(lbl,col) in enumerate([("PI",PURPLE),("Manager",BLUE),("Member",SLATE)]):
    sq=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(10.75+i*0.86),Inches(0.27),Inches(0.16),Inches(0.16))
    sq.fill.solid(); sq.fill.fore_color.rgb=col; sq.line.fill.background(); sq.shadow.inherit=False
    textbox(s,lbl,10.94+i*0.86,0.2,0.7,0.3,size=9,color=WHITE)

# ---- TOP SPINE: users -> login -> app <-> supabase -> backups
textbox(s,"USERS",0.35,0.95,1.5,0.3,size=11,color=GREY,bold=True)
pi =box(s,0.35,1.28,1.55,0.44,"PI",fill=PURPLE,size=12)
mgr=box(s,0.35,1.78,1.55,0.44,"Manager",fill=BLUE,size=12)
mem=box(s,0.35,2.28,1.55,0.44,"Member",fill=SLATE,size=12)
login=box(s,2.55,1.45,2.05,0.95,"Log in",fill=DBLUE,size=12,sub="name + shared password · email once")
app =box(s,5.05,1.4,2.5,1.05,"Colony web app",fill=BLUE,size=13,sub="index.html · GitHub Pages")
sb  =box(s,10.15,1.25,2.95,1.05,"Supabase",fill=GREEN,size=13,sub="Postgres + RLS + auto REST API")
tbl =box(s,10.15,2.42,2.95,0.5,"mice · app_users · requests · audit_log",fill=DGREEN,size=10)
bkp =box(s,10.15,3.06,2.95,0.5,"Daily backups (GitHub Actions)",fill=AMBER,size=11)

for u in (pi,mgr,mem): connect(s,R(u),L(login))
connect(s,R(login),L(app))
connect(s,R(app),L(sb),two=True); note(s,"reads / writes  (public key + RLS)",7.4,1.5,2.9,color=GREY)
connect(s,B(sb),T(tbl)); connect(s,B(tbl),T(bkp))

# ---- MIDDLE: what anyone can do in the app
textbox(s,"In the app, anyone can:",5.0,2.7,4.0,0.3,size=11,color=GREY,bold=True,italic=True)
add =box(s,2.55,3.15,2.35,0.9,"Add cohort (by cage)",fill=BLUE,size=12,sub="or Import CSV / Excel")
brw =box(s,5.05,3.15,2.4,0.9,"Browse the colony",fill=SLATE,size=12,sub="search · filter · Grouped view")
myc =box(s,7.6,3.15,2.4,0.9,"My colony",fill=PURPLE,size=12,sub="only YOUR cohorts")
connect(s,B(app),T(add)); connect(s,B(app),T(brw)); connect(s,B(app),T(myc))
note(s,"↑ owner-scoped: you see the mice you own",7.4,4.06,2.8,color=AMBER)

# ---- BOTTOM: request & approval + email pipeline
textbox(s,"Requests & email notifications:",0.35,4.55,5.0,0.3,size=11,color=GREY,bold=True,italic=True)
req =box(s,0.35,4.9,2.35,1.0,"File a request",fill=BLUE,size=12,sub="specific mouse # or by criteria")
rte =box(s,3.0,4.9,2.75,1.0,"Match a live mouse → Owner",fill=GREEN,size=12,sub="none available → Breeding queue")
app2=box(s,6.05,4.9,2.55,1.0,"Approve / transfer / route",fill=AMBER,size=12,sub="Manager or PI only")
noti=box(s,8.9,4.72,4.2,0.62,"Notify: Owner · Managers · PI",fill=PURPLE,size=12)
send=box(s,8.9,5.5,4.2,0.9,"Edge Function → Resend → emails",fill=DBLUE,size=11,sub="fallback: pre-filled draft email")
connect(s,B(mem),(1.5,4.9),color=CONN,dash=True)   # a member starts a request
connect(s,R(req),L(rte)); connect(s,R(rte),L(app2))
connect(s,R(app2),L(noti)); connect(s,B(noti),T(send))
note(s,"role decides who approves & who gets emailed",5.9,5.95,2.9,color=AMBER)

# ---- takeaway strip
strip=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(0.35),Inches(6.75),Inches(12.65),Inches(0.55))
strip.fill.solid(); strip.fill.fore_color.rgb=RGBColor(0xEF,0xF3,0xFB); strip.line.color.rgb=BLUE
strip.line.width=Pt(1); strip.shadow.inherit=False
tf=strip.text_frame; tf.vertical_anchor=MSO_ANCHOR.MIDDLE; p=tf.paragraphs[0]; p.alignment=PP_ALIGN.CENTER
r=p.add_run()
r.text=("Same data, different views: everyone browses & adds · 'My colony' is scoped to you · "
        "only Managers/PI approve & route to breeding · every change is logged in audit_log")
r.font.size=Pt(12); r.font.color.rgb=DBLUE; r.font.name="Calibri"; r.font.bold=True

out="/home/exx/leelab-colony/docs/Colony_DB_Overview.pptx"; prs.save(out)
print("saved",out,"slides:",len(prs.slides._sldIdLst))

# overlap sanity check on boxes
boxes={"pi":pi,"mgr":mgr,"mem":mem,"login":login,"app":app,"sb":sb,"tbl":tbl,"bkp":bkp,
       "add":add,"brw":brw,"myc":myc,"req":req,"rte":rte,"app2":app2,"noti":noti,"send":send}
def ov(a,b):
    return not (a["l"]+a["w"]<=b["l"] or b["l"]+b["w"]<=a["l"] or a["t"]+a["h"]<=b["t"] or b["t"]+b["h"]<=a["t"])
names=list(boxes); hit=[]
for i in range(len(names)):
    for j in range(i+1,len(names)):
        if ov(boxes[names[i]],boxes[names[j]]): hit.append((names[i],names[j]))
print("overlaps:",hit if hit else "none")
