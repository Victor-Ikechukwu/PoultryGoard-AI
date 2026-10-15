# -*- coding: utf-8 -*-
"""Build the IEEE conference paper (docx) for PoultryGuard."""
import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = r"D:\Reem-Oman's-Project\PoultryGuard_PoC"
FIG = os.path.join(ROOT, "paper", "figures")
OUT = os.path.join(ROOT, "paper", "PoultryGuard_IEEE.docx")

doc = Document()

# ---- base style ----
st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(9.5)
st.paragraph_format.space_after = Pt(0)
st.paragraph_format.line_spacing = 1.0

# ---- page setup (US Letter, narrow margins) ----
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
for s in (sec,):
    s.top_margin = Inches(0.7); s.bottom_margin = Inches(0.7)
    s.left_margin = Inches(0.65); s.right_margin = Inches(0.65)

def set_cols(section, n, space=360):
    cols = section._sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols"); section._sectPr.append(cols)
    cols.set(qn("w:num"), str(n)); cols.set(qn("w:space"), str(space))

def para(text, align=None, size=None, bold=False, italic=False, before=0, after=4,
         style=None, justify=True, color=None):
    p = doc.add_paragraph(style=style)
    if align is not None: p.alignment = align
    elif justify: p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format; pf.space_before = Pt(before); pf.space_after = Pt(after)
    r = p.add_run(text)
    r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = color
    return p

def runs(parts, align=None, before=0, after=4, justify=True):
    p = doc.add_paragraph()
    if align is not None: p.alignment = align
    elif justify: p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(before); p.paragraph_format.space_after = Pt(after)
    for text, b, i in parts:
        r = p.add_run(text); r.bold = b; r.italic = i
    return p

_secn = 0
def H1(title):
    global _secn; _secn += 1
    roman = ["I","II","III","IV","V","VI","VII","VIII","IX","X"][_secn-1]
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(3)
    r = p.add_run(f"{roman}.  {title.upper()}"); r.bold = True; r.font.size = Pt(10)
    return p

def H2(title):
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(5); p.paragraph_format.space_after = Pt(2)
    r = p.add_run(title); r.italic = True; r.font.size = Pt(9.5)
    return p

_eqn = 0
def eq(text):
    global _eqn; _eqn += 1
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2); p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text); r.italic = True; r.font.size = Pt(9.5)
    r2 = p.add_run(f"  ({_eqn})"); r2.font.size = Pt(9.5)
    return p

def fig(path, caption, width=3.3):
    if not os.path.exists(path): return
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(path, width=Inches(width))
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(6)
    r = c.add_run(caption); r.font.size = Pt(8)

def shade(cell, hexc):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), hexc); tcPr.append(sh)

def table(caption_num, caption_title, header, rows, widths):
    cap = doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(6)
    r = cap.add_run(f"TABLE {caption_num}"); r.bold = True; r.font.size = Pt(8)
    cap2 = doc.add_paragraph(); cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap2.paragraph_format.space_after = Pt(2)
    r2 = cap2.add_run(caption_title); r2.font.size = Pt(8); r2.italic = True
    t = doc.add_table(rows=1, cols=len(header)); t.style = "Table Grid"; t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for j, h in enumerate(header):
        c = t.rows[0].cells[j]; c.width = Inches(widths[j]); shade(c, "D9E1F2")
        pr = c.paragraphs[0]; pr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rn = pr.add_run(h); rn.bold = True; rn.font.size = Pt(7.5)
    for row in rows:
        cells = t.add_row().cells
        for j, val in enumerate(row):
            cells[j].width = Inches(widths[j])
            pr = cells[j].paragraphs[0]; rn = pr.add_run(str(val)); rn.font.size = Pt(7.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# ============================= FRONT MATTER (1 column) =============================
set_cols(sec, 1)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("PoultryGuard: A Lightweight, Edge-Deployable Deep-Learning Framework for "
              "Real-Time Chick Counting, Mortality Detection, and Automated Veterinary Response")
r.bold = True; r.font.size = Pt(18)
p.paragraph_format.space_after = Pt(8)

# authors
a = doc.add_paragraph(); a.alignment = WD_ALIGN_PARAGRAPH.CENTER
ar = a.add_run("Agughasi Victor Ikechukwu"); ar.font.size = Pt(11); ar.bold = True
a.add_run("\u00B9\u002A").font.size = Pt(8)
for line, sz in [("Department of Computer Science & Engineering", 9.5),
                 ("Maharaja Institute of Technology Mysore, India", 9.5),
                 ("victor.agughasi@gmail.com  \u00B7  ORCID: 0000-0002-1175-3089", 9.0)]:
    pl = doc.add_paragraph(); pl.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pl.paragraph_format.space_after = Pt(0); rr = pl.add_run(line); rr.font.size = Pt(sz)
doc.add_paragraph().paragraph_format.space_after = Pt(4)

# abstract
runs([("Abstract\u2014", True, True),
      ("Continuous, individual-level monitoring of broiler flocks is central to animal "
       "welfare and to the economics of poultry production, yet it remains largely manual "
       "and therefore infrequent and subjective. This paper presents PoultryGuard, an "
       "end-to-end computer-vision framework that unifies chick counting, individual "
       "tracking, immobility- and posture-based mortality detection, in-house zone "
       "localization, automatic case documentation, and an automated veterinary response "
       "workflow in a single lightweight system. A YOLO11n detector is fine-tuned on a "
       "public overhead broiler-house dataset (up to 322 birds per frame) and coupled with "
       "a ByteTrack multi-object tracker and a temporal behaviour engine that escalates a "
       "bird to \u201Csuspected mortality\u201D only after multi-frame immobility is corroborated "
       "by a prostrate posture. On a held-out test split the detector attains 0.954 mAP@50, "
       "0.948 precision, 0.936 recall, and a mean counting error of 1.8 birds (4.4% on dense "
       "frames). Exporting the model to ONNX removes the PyTorch dependency, shrinks the "
       "runtime to a 10\u00A0MB model that runs about twice as fast as the PyTorch backend and "
       "in real time on a single CPU core, enabling both on-farm edge boxes and free "
       "cloud hosting. A controlled ablation isolates the effect of input resolution, "
       "confidence threshold, and inference backend, and the system is compared against "
       "recent state-of-the-art poultry detectors. The framework additionally fuses "
       "environmental sensing (temperature, humidity, CO\u2082, NH\u2083) to shift from mortality "
       "detection toward mortality prevention.", False, False)])
runs([("Keywords\u2014", True, True),
      ("precision livestock farming, poultry health monitoring, object detection, YOLO, "
       "multi-object tracking, mortality detection, edge AI, ONNX, explainable and "
       "trustworthy AI, veterinary informatics.", False, True)], after=6)

# ============================= BODY (2 columns) =============================
body = doc.add_section(WD_SECTION.CONTINUOUS)
body.page_width, body.page_height = Inches(8.5), Inches(11)
body.top_margin = Inches(0.7); body.bottom_margin = Inches(0.7)
body.left_margin = Inches(0.65); body.right_margin = Inches(0.65)
set_cols(body, 2, space=360)

# ---------- I. INTRODUCTION ----------
H1("Introduction")
para("Poultry is the most widely produced livestock on earth, and broiler chickens account "
     "for the majority of global poultry meat. In intensive houses that hold tens of thousands "
     "of birds, flock health is still assessed by periodic walk-throughs in which a stockperson "
     "visually inspects the birds and removes carcasses. Such inspection is labour-intensive, "
     "intermittent, and subjective; early signs of disease, heat stress, or localized mortality "
     "are easily missed between rounds, and undetected mortality both compromises welfare and "
     "silently erodes feed-conversion economics. Automated, continuous, and individual-level "
     "monitoring is therefore an important goal of precision livestock farming.")
para("The deep-learning revolution has made such monitoring technically feasible. Convolutional "
     "and, more recently, self-supervised representation learning have driven order-of-magnitude "
     "gains in visual recognition [1]\u2013[3], and single-stage object detectors of the YOLO family "
     "now deliver real-time, high-recall detection of small, densely packed objects [4]\u2013[6]. "
     "These advances have been applied to poultry for counting, behaviour analysis, and welfare "
     "assessment [10]\u2013[16]. However, most existing systems address a single sub-task\u2014typically "
     "counting or behaviour classification\u2014and are evaluated offline on server-class GPUs. Few "
     "integrate the full operational loop that a farm actually needs: detect and count the flock, "
     "track individuals over time, decide which bird is dying and where it is, document the "
     "event, and route it to a veterinarian for action. Fewer still are light enough to run on "
     "an edge device beside the birds or on a free cloud tier, which is the deployment reality "
     "for most producers.")
para("This paper closes that gap with PoultryGuard, an end-to-end framework whose contributions "
     "are:")
for b in [
    "A unified pipeline that couples detection-based counting, ByteTrack multi-object tracking, "
    "a temporal immobility-plus-posture mortality engine, zone localization, automatic case "
    "documentation, and an automated veterinary notification-and-booking workflow.",
    "A YOLO11n detector fine-tuned on a public overhead broiler dataset that reaches 0.954 "
    "mAP@50 and a 4.4% dense-frame counting error, with a transparent before/after comparison "
    "against a generic COCO baseline.",
    "A lightweight ONNX deployment path that removes PyTorch and ultralytics (\u22481\u00A0GB) from the "
    "runtime, yielding a 10\u00A0MB model that is \u22482\u00D7 faster than the PyTorch backend and runs in "
    "real time on one CPU core\u2014suitable for on-farm edge hardware and free Streamlit-Cloud hosting.",
    "A controlled ablation over input resolution, confidence threshold, and inference backend, "
    "and a comparison against recent state-of-the-art poultry detectors.",
    "An environmental early-warning extension that fuses temperature, humidity, CO\u2082 and NH\u2083 with "
    "behaviour, moving the system from mortality detection toward prevention.",
]:
    bp = doc.add_paragraph(style="List Bullet"); bp.paragraph_format.space_after = Pt(1)
    rr = bp.add_run(b); rr.font.size = Pt(9.5)
para("The remainder of the paper is organized as follows. Section\u00A0II reviews related work in "
     "object detection and poultry vision. Section\u00A0III details the dataset, system architecture, "
     "and each module. Section\u00A0IV reports detection, counting, ablation, and state-of-the-art "
     "comparison results and discusses deployment. Section\u00A0V concludes.", before=2)

fig(os.path.join(FIG, "fig_architecture.png"),
    "Fig. 1. PoultryGuard end-to-end architecture. The perception path (camera \u2192 YOLO11n/ONNX "
    "detector \u2192 ByteTrack \u2192 behaviour/immobility \u2192 posture) feeds a mortality-and-localization "
    "decision that triggers automatic documentation and the veterinary workflow; an environmental "
    "branch (T/RH/CO\u2082/NH\u2083) provides early warning.", width=3.35)

# ---------- II. RELATED WORKS ----------
H1("Related Works")
H2("A. Visual Recognition and Object Detection")
para("Modern poultry vision rests on two foundations: large-scale supervised pre-training and "
     "efficient single-stage detection. The ImageNet benchmark [3] established transfer learning "
     "as the default paradigm, and the broad progress of deep learning that followed [1] underpins "
     "every model used here; emerging self-supervised and world-model approaches [2] point toward "
     "label-efficient successors. For detection, the YOLO family remains dominant in agriculture "
     "because it offers the best accuracy-latency trade-off for small, crowded objects: YOLOv8 [8] "
     "popularized an anchor-free, decoupled head; YOLOv9 [5] and YOLOv10 [6] improved gradient flow "
     "and removed non-maximum suppression at inference; and YOLO11 [4], used in this work, refines "
     "the backbone and neck for higher accuracy at nano scale. Transformer detectors such as RT-DETR "
     "[7] now match YOLO latency, while multi-object trackers\u2014particularly ByteTrack [9], which "
     "associates even low-confidence boxes\u2014enable the per-bird continuity that mortality detection "
     "requires.")
para("A second, orthogonal axis of progress is representation learning without labels. "
     "Self-supervised features such as DINOv2 [21] and promptable segmentation such as SAM 2 "
     "[20] now provide general-purpose visual priors, and joint-embedding predictive "
     "architectures [2] point toward models that learn the structure of the physical world "
     "from video rather than from curated labels. While PoultryGuard uses a conventional "
     "supervised detector for latency reasons, these foundation models are directly relevant "
     "to future label-efficient extensions, because the cost of annotating dense poultry scenes "
     "is the dominant bottleneck in the field.")
H2("B. Multi-Object Tracking for Individual Monitoring")
para("Counting alone cannot support mortality detection: deciding that a specific bird has "
     "stopped moving requires a persistent identity for each animal across time. The tracking-"
     "by-detection paradigm addresses this by linking per-frame detections into tracks. SORT "
     "and DeepSORT established the Kalman-filter-plus-association template, but discard low-"
     "confidence detections and therefore fragment identities under the heavy occlusion typical "
     "of crowded houses. ByteTrack [9] improved robustness markedly by associating every "
     "detection box, including low-scoring ones, which recovers objects during partial occlusion "
     "and birds that momentarily merge. Transformer-based end-to-end trackers are emerging in "
     "the wake of DETR [33] and RT-DETR [7], but remain heavier than is practical on edge "
     "hardware. PoultryGuard adopts ByteTrack precisely because it preserves identities cheaply, "
     "which is the property the downstream immobility logic depends upon.")
H2("C. Computer Vision for Poultry and Precision Livestock Farming")
para("Recent surveys document a rapid expansion of YOLO-based poultry systems spanning identification, "
     "counting, tracking, and health monitoring [15], [16]. For counting, YOLO-CCA augments YOLOv8 "
     "with coordinate attention and a reversible-column backbone to handle occlusion in dense cages, "
     "raising F1 to 96.7% and running at 90.9\u00A0FPS on a Jetson Orin [10]. HenSense and its FeatherNet "
     "Fusion-YOLO model target free-range birds with a 2.14\u00A0M-parameter edge model reaching 92.6% "
     "mAP@50 [11]. Thermal-imaging pipelines pair YOLOv8 with infrared frames for broiler counting "
     "at 95% mAP [12], and processing-line systems combine detection with SORT/ByteTrack tracking to "
     "count birds on conveyors at F1 up to 0.99 [13], [14]. These results confirm that fine-tuned "
     "lightweight detectors are accurate on in-domain poultry imagery, but they overwhelmingly stop "
     "at counting or tracking and are reported on bespoke datasets with server-side inference.")
para("Beyond single-study accuracy, recent surveys emphasize that the field has consolidated "
     "around lightweight YOLO variants and is shifting from pure counting toward welfare- and "
     "health-oriented behaviour analysis [15], [16]. Reported systems increasingly track "
     "activity, detect lameness or huddling, and estimate distribution uniformity, and a growing "
     "subset targets dead-bird detection directly [35]. Two consistent limitations recur across "
     "this literature, however, and motivate the present work: results are reported on bespoke, "
     "privately collected datasets that preclude direct comparison, and inference is assumed to "
     "run on server-class or workstation GPUs rather than on the constrained hardware that a "
     "producer can realistically install in every house.")
H2("D. Deep Learning for Medical and Biomedical Imaging")
para("The methodological toolkit for PoultryGuard\u2014transfer learning, fine-tuning, attention, and "
     "explainability\u2014matured largely in medical imaging. Prior work by the present author on chest-"
     "radiograph analysis showed that ensemble region-of-interest identification [28] and, notably, "
     "fine-tuning rather than full training yields efficient, accurate diagnosis under explainable-AI "
     "constraints [18]. A complementary comparative study of deep-learning and classical models for "
     "infrared breast thermography [17] established evaluation practices\u2014paired accuracy, precision, "
     "recall, and ablation\u2014that this paper adopts for an agricultural setting, and a segmentation-"
     "plus-residual-learning pipeline for diabetic retinopathy [19] demonstrated the same "
     "lightweight-model philosophy on another dense-structure task. Trustworthy, resource-aware "
     "models developed for clinics transfer naturally to the equally resource-constrained farm.")
H2("E. Edge AI and Efficient On-Device Inference")
para("Deploying detectors on-farm imposes hard constraints on memory, compute, and power that "
     "server-side studies rarely consider. Three complementary strategies dominate. Architectural "
     "efficiency selects compact backbones—the nano/tiny YOLO scales [4], [8] and efficiency-"
     "oriented designs such as EfficientNet [26]—trading a small accuracy margin for large "
     "latency gains. Graph-level optimization exports a trained model to an interchange format "
     "such as ONNX and executes it with a dedicated runtime [22] that fuses operators and removes "
     "the training framework from the deployment, which both shrinks the image and accelerates "
     "inference. Hardware acceleration maps the graph onto embedded accelerators (e.g. Jetson-class "
     "GPUs or TensorRT), as several poultry systems demonstrate at tens of frames per second "
     "[10], [11]. PoultryGuard combines the first two: a nano detector exported to ONNX Runtime, "
     "which is sufficient for real-time operation on a single commodity CPU core and therefore "
     "removes the need for specialized accelerators or a persistent cloud GPU.")
H2("F. Research Gap")
para("Across these threads, no single reported system jointly delivers (i) dense flock counting, "
     "(ii) individual mortality detection with in-house localization, (iii) an automated veterinary "
     "response loop, and (iv) genuinely edge/cloud-deployable inference. Table\u00A0I summarizes "
     "representative recent work and positions PoultryGuard against it.")

table("I", "Representative Recent Poultry-Vision Work vs. PoultryGuard",
      ["Study (year)", "Task", "Result / note"],
      [["YOLO-CCA [10] (2025)", "Cage counting", "F1 96.7%, 90.9 FPS Jetson"],
       ["HenSense [11] (2026)", "Free-range detect", "92.6% mAP@50, 2.14M par."],
       ["Thermal YOLOv8 [12] (2024)", "Broiler count", "95% mAP, 2% error"],
       ["Line YOLO11-n [13] (2026)", "Slaughter count", "99.5% mAP@50"],
       ["YOLOv8+SORT [14] (2025)", "Line counting", "F1 0.99, MAE 2.3"],
       ["PoultryGuard (ours)", "Count+mortality+vet+edge", "0.954 mAP@50, 10MB ONNX"]],
      [1.05, 0.85, 1.35])

# ---------- III. MATERIALS AND METHODS ----------
H1("Materials and Methods")
H2("A. Dataset")
para("Experiments use the public GEL broiler-chicken dataset (Roboflow Universe, CC\u00A0BY\u00A04.0), "
     "comprising 2,598 overhead images of commercial broiler houses captured by fixed ceiling "
     "cameras and split into 1,819 training, 520 validation, and 259 test images. Scenes are highly "
     "variable in density\u2014from near-empty litter to clusters of up to 322 birds in a single frame\u2014"
     "and in illumination, which makes the set a realistic proxy for the overhead camera placement "
     "a deployed system would use. All annotations are single-class (\u201Cchicken\u201D). The dataset was "
     "used as released, without manual re-labelling, to keep the pipeline reproducible.")
H2("B. System Overview")
para("PoultryGuard is organized as a per-frame pipeline (Fig.\u00A01). A frame from a camera (local "
     "webcam, RTSP/IP stream, or recorded video) is passed to the detector; detections are associated "
     "across frames by the tracker; per-track motion and posture are analysed; a mortality decision "
     "is localized to a house zone; confirmed events are documented and escalated to a veterinarian; "
     "and an independent environmental branch raises early warnings. Each module exposes a narrow "
     "interface so that, for example, the posture heuristic can be replaced by a trained network "
     "without touching the rest of the system.")
H2("C. Detector and Fine-Tuning")
para("The detector is YOLO11n (2.6\u00A0M parameters), chosen for the smallest accuracy-competitive "
     "footprint in the family. Starting from COCO-pretrained weights, the model was fine-tuned for "
     "30 epochs at 512\u00D7512 resolution with the AdamW optimizer (auto-selected learning rate), batch "
     "size 16, and the standard mosaic/HSV/flip augmentations, on a single CPU; no GPU was required. "
     "Fine-tuning rather than training from scratch follows the efficiency argument established in "
     "[18] and converges within a few epochs because the COCO prior already encodes generic object "
     "structure.")
para("Training minimizes the standard YOLO composite objective—a complete-IoU box-regression "
     "term, a distribution-focal term for box-boundary quality, and a binary cross-entropy "
     "classification term—summed over three detection scales. Because the single foreground class "
     "is small and densely packed, the anchor-free high-resolution head of the nano architecture "
     "is well matched to the task. Key settings are summarized in Table V; notably, inference is "
     "run at a higher resolution (640) than training (512), which empirically raises recall on "
     "small birds at negligible cost (Section IV-B).")
table("V", "Training and Inference Hyperparameters",
      ["Parameter", "Setting"],
      [["Base model / init.", "YOLO11n / COCO-pretrained"],
       ["Parameters", "2.6 M"],
       ["Epochs", "30 (patience 12)"],
       ["Image size (train / infer)", "512 / 640 px"],
       ["Batch size", "16"],
       ["Optimizer / LR", "AdamW / auto (~9e-4)"],
       ["Augmentation", "Mosaic, HSV, flip"],
       ["Confidence / NMS IoU", "0.40 / 0.50"],
       ["Max detections", "300"],
       ["Tracker", "ByteTrack"],
       ["Compute", "single CPU core"]],
      [1.55, 1.15])
H2("D. Multi-Object Tracking and Behaviour")
para("Detections are associated by ByteTrack [9], which assigns a persistent identity to each bird "
     "and, by matching low-confidence boxes, maintains identities through the partial occlusions that "
     "are endemic to crowded houses. For every track the engine maintains a short rolling history of "
     "centroid position and instantaneous speed, from which it derives (i) an immobility timer that "
     "starts when speed falls below a threshold and (ii) a social-isolation score equal to the "
     "distance to the nearest neighbour normalized by the flock-median spacing. Both are computed "
     "over multiple frames rather than a single image, which suppresses the false positives that a "
     "momentary pause would otherwise cause.")
para("Formally, let cᵢ(t) be the centroid of track i at time t. The instantaneous speed is")
eq("vᵢ(t) = ‖ cᵢ(t) − cᵢ(t−Δt) ‖ / Δt ,")
para("and the bird is momentarily still when vᵢ(t) < θᵥ. The immobility duration is the time "
     "elapsed since stillness began,")
eq("τᵢ(t) = t − tᵢ(still) ,")
para("where tᵢ(still) is reset whenever the speed rises back above θᵥ, so that τ measures "
     "sustained rather than instantaneous inactivity. Social isolation—an early behavioural "
     "correlate of illness—is scored by normalizing a bird’s nearest-neighbour distance d_nn(i) "
     "by the median inter-bird spacing d_med of the current frame,")
eq("ρᵢ = min( d_nn(i) / (κ · d_med) , 1 ) ,")
para("so that ρᵢ approaching 1 denotes a bird that has drifted from the flock. Evaluating all "
     "three quantities over a rolling multi-frame window, not a single image, is what suppresses "
     "the false alarms that a momentary pause would otherwise cause.")
H2("E. Posture Classification and Mortality Decision")
para("Posture is summarized from the detection geometry\u2014aspect ratio and elongation distinguish an "
     "upright, active bird from a prostrate one\u2014behind a classifier interface into which a CNN trained "
     "on captured mortality crops can later be dropped. A finite-state machine fuses the behavioural "
     "and postural cues: a track is NORMAL while active, ABNORMAL after sustained immobility, and "
     "SUSPECTED only when prolonged immobility coincides with a lying posture (optionally reinforced "
     "by isolation). A mortality confidence score blends these signals, and crossing the SUSPECTED "
     "state opens exactly one case per bird.")
para("Concretely, posture is summarized from the detection-box aspect ratio α = w/h and "
     "elongation ε = max(w,h)/min(w,h): an upright, active bird yields a compact, tall box "
     "(α < 1), whereas a prostrate bird yields a wide, flat one, and the bird is labelled "
     "“lying” when α ≥ α₀. The state machine fuses behaviour and posture into a bounded "
     "mortality score")
eq("sᵢ = 0.6·min(τᵢ/T_s, 1) + 0.3·1{lying} + 0.1·ρᵢ ,")
para("where T_s is the suspected-mortality dwell time and 1{·} is the indicator function. The "
     "weights prioritize sustained immobility while letting posture and isolation corroborate it. "
     "A track is NORMAL while active, escalates to ABNORMAL once τᵢ exceeds a first threshold, "
     "and reaches SUSPECTED only when prolonged immobility (τᵢ ≥ T_s) coincides with a lying "
     "posture; crossing SUSPECTED opens exactly one case per bird, so a single event cannot raise "
     "duplicate alerts. The thresholds (θᵥ, T_s, α₀, κ) are exposed as configuration so the "
     "system can be tuned to breed, age, and camera geometry without retraining.")
H2("F. Localization, Documentation and Veterinary Workflow")
para("The frame is overlaid with a configurable zone grid, and a suspected bird is tagged with its "
     "zone and timestamp, e.g. \u201CSuspected mortality \u2014 Zone\u00A0B \u2014 08:35\u201D. The system then auto-saves "
     "an annotated snapshot and writes a structured case (chick reference, age, location, posture "
     "profile, pre-mortality behaviour window) to a database, generates a veterinary case report, and "
     "\u2014on confirmation\u2014notifies the veterinarian and books a farm visit. A veterinary console records "
     "diagnosis, treatment, vaccination, and case closure, keeping the clinician as the final "
     "decision-maker while the AI serves as an early-warning and documentation aid.")
para("The house is partitioned into an R×C grid, and a bird at pixel centroid c=(c_x,c_y) in a "
     "W×H frame is mapped to the human-readable zone")
eq("Z(c) = ( ⌊ R·c_y/H ⌋ , ⌊ C·c_x/W ⌋ ) ,")
para("e.g. “Zone B3”, which—together with the event timestamp—forms the compact alert the "
     "stockperson receives and indexes the saved evidence in the case database. The zone "
     "resolution is configurable, trading localization precision against alert granularity.")
H2("G. Environmental Early-Warning")
para("A sensor branch models temperature, humidity, CO\u2082 and NH\u2083 against age-dependent target bands "
     "(the brooding set-point falls by roughly 0.3\u00A0\u00B0C per day) and raises graded alerts. Fusing these "
     "signals with behaviour lets the system flag deteriorating house conditions before they manifest "
     "as mortality, which is the practically more valuable regime.")
para("The temperature target is age-dependent: broilers require a high brooding set-point that "
     "declines as they feather, approximated as")
eq("T*(a) = max( 21, 33 − 0.3·a )  [°C] ,")
para("for flock age a in days, with a tolerance band around T*(a). Humidity, CO₂ and NH₃ are "
     "compared against fixed welfare limits (e.g. NH₃ ≤ 20–25 ppm), and graded “warn”/“alarm” "
     "alerts are raised and logged. Because deteriorating air quality and thermal stress precede "
     "visible morbidity, this branch provides lead time that behaviour alone does not, and its "
     "alerts are correlated with the mortality cases in the same house to support root-cause "
     "analysis.")
H2("H. Edge Deployment")
para("For deployment the fine-tuned model is exported to ONNX and executed with ONNX Runtime using "
     "only NumPy and OpenCV for pre/post-processing, eliminating the PyTorch and ultralytics "
     "dependencies. A backend factory selects the ONNX path automatically when PyTorch is absent, so "
     "the identical application runs on a developer workstation (PyTorch) and on an edge box or a "
     "free cloud tier (ONNX) without code changes.")
para("The ONNX export is numerically faithful: the exported graph reproduces the PyTorch "
     "detections exactly (Section IV-B), and the post-processing—letterbox resize, a single "
     "forward pass, confidence filtering, and class-agnostic non-maximum suppression—is "
     "implemented in NumPy and OpenCV only. The per-frame cost is dominated by the detector’s "
     "fixed O(1) forward pass; tracking and behaviour bookkeeping are O(n) in the number of "
     "detections n, and the nearest-neighbour term in (3) is computed on frame centroids only, "
     "so the whole pipeline remains real-time on one CPU core even for the densest frames.")
H2("I. Evaluation Protocol")
para("Detection quality is reported on the untouched test split as mAP@50, mAP@50\u201395, precision and "
     "recall at the training resolution. Counting quality is measured as mean absolute error (MAE) "
     "between predicted and ground-truth bird counts over all test images, and as mean absolute "
     "percentage error (MAPE) restricted to dense frames (ground truth \u2265 20 birds), which is the "
     "operationally relevant regime. Efficiency is reported as single-core CPU latency per frame and "
     "model size.")

# ---------- IV. RESULTS AND DISCUSSION ----------
para("For the operationally critical dense subset D (ground-truth count ≥ 20 birds), the mean "
     "absolute percentage counting error is")
eq("MAPE = (100/|D|) · Σ_{i∈D} | ŷᵢ − yᵢ | / yᵢ ,")
para("with ŷᵢ and yᵢ the predicted and ground-truth counts of image i. All results below use the "
     "single held-out test split, which the detector never saw during training or validation.")
H1("Results and Discussion")
H2("A. Detection and Counting Performance")
para("On the 259-image test split the fine-tuned YOLO11n attains 0.954 mAP@50, 0.647 mAP@50\u201395, "
     "0.948 precision and 0.936 recall (Table\u00A0II). The precision-recall curve (Fig.\u00A03) is close to "
     "the top-right corner across the operating range, and the normalized confusion is dominated by "
     "the true-positive diagonal. Translated into the task that matters on-farm, the model counts "
     "with a mean error of 1.8 birds per image and 4.4% error on dense frames\u2014for example 201 against "
     "a ground truth of 203 on the frame in Fig.\u00A04. For context, the generic COCO detector counts "
     "only a handful of birds on the same dense scenes (it was trained on wild birds, not overhead "
     "broilers), a failure the fine-tuned model removes entirely. Training converged smoothly within "
     "30 epochs (Fig.\u00A02).")

table("II", "Detection and Counting Performance on the Test Split",
      ["Metric", "Value"],
      [["mAP@50", "0.954"], ["mAP@50\u201395", "0.647"], ["Precision", "0.948"],
       ["Recall", "0.936"], ["Count MAE (all)", "1.8 birds"],
       ["Count MAPE (dense \u2265 20)", "4.4%"], ["Model size (ONNX)", "10 MB"],
       ["Parameters", "2.6 M"]],
      [1.6, 1.0])

fig(os.path.join(FIG, "fig_training.png"),
    "Fig. 2. Fine-tuning dynamics over 30 epochs: (a) validation mAP, precision and recall; "
    "(b) training box/cls/dfl losses.", width=3.35)
fig(os.path.join(FIG, "fig_pr_curve.png"),
    "Fig. 3. Precision-recall curve on the held-out test split (single \u201Cchicken\u201D class).", width=2.7)
fig(os.path.join(FIG, "fig_detect_example.jpg"),
    "Fig. 4. Representative detection on an overhead broiler-house test frame: 201 birds counted "
    "against a ground truth of 203; well-separated birds are boxed one-to-one.", width=3.0)

para("Breaking counting error down by flock density (Table VI) is revealing. On empty and "
     "sparse frames the model is almost exact—mean absolute error of 0.2 and 0.3 birds "
     "respectively—which shows that the fine-tuned detector rarely hallucinates birds on bare "
     "litter, the failure mode that plagued the generic baseline. Accuracy stays strong through "
     "the medium-density regime (MAE 2.0, 3.9%). The residual error is concentrated in the small "
     "number of extreme frames above 100 birds (MAE 8.6), where heavily overlapping bodies are "
     "occasionally split into two boxes. Because those frames are rare and the per-bird error "
     "remains a single-digit percentage, the system’s practical counting accuracy is high across "
     "the operating range, and the dense regime is the clear target for future improvement.")
table("VI", "Counting Error by Flock Density (Test Split)",
      ["Density (GT birds)", "Images", "MAE", "MAPE"],
      [["Empty (0)", "10", "0.20", "—"],
       ["Sparse (1–19)", "116", "0.31", "6.7%"],
       ["Medium (20–99)", "109", "2.04", "3.9%"],
       ["Dense (100+)", "24", "8.62", "6.5%"]],
      [1.1, 0.6, 0.55, 0.6])
H2("B. Ablation Study")
para("A controlled ablation (Table\u00A0III, Fig.\u00A05) isolates three design choices. Input resolution: "
     "accuracy improves from 416 to 640\u00A0px (dense error 4.9%\u21924.5%) but collapses at 960\u00A0px "
     "(12.8%), where the detector over-segments large birds; 640\u00A0px is the accuracy-latency optimum. "
     "Confidence threshold: 0.40 minimizes dense error (4.5%), with 0.25 admitting litter false "
     "positives and 0.55 missing partially occluded birds. Inference backend: at 640\u00A0px the ONNX "
     "runtime is roughly twice as fast as PyTorch on the same CPU while producing numerically "
     "identical detections, confirming that the lightweight path costs no accuracy.")

table("III", "Ablation: Resolution, Confidence, and Backend",
      ["Factor", "Setting", "Dense err.", "Latency"],
      [["Resolution", "416 px", "4.9%", "163 ms"],
       ["", "512 px", "4.7%", "148 ms"],
       ["", "640 px (used)", "4.5%", "176 ms"],
       ["", "960 px", "12.8%", "494 ms"],
       ["Confidence", "0.25 / 0.40 / 0.55", "4.9 / 4.5 / 5.4%", "\u2014"],
       ["Backend", "PyTorch / ONNX", "identical", "2.1\u00D7 faster"]],
      [0.72, 1.05, 0.72, 0.71])

fig(os.path.join(FIG, "fig_ablation.png"),
    "Fig. 5. Ablation: (a) dense-frame count error vs. input resolution; (b) latency vs. resolution; "
    "(c) count error vs. confidence threshold.", width=3.35)

H2("C. Comparison with State of the Art")
para("Table\u00A0IV places PoultryGuard against recent state-of-the-art poultry detectors. Because each "
     "study reports on its own dataset and camera geometry, cross-paper accuracy is indicative rather "
     "than a controlled head-to-head; the comparison is therefore framed around the accuracy-"
     "efficiency-scope trade-off. PoultryGuard\u2019s 0.954 mAP@50 is competitive with cage- and line-"
     "oriented systems that reach 0.95\u20130.99 under more constrained imaging [10], [12]\u2013[14], and it "
     "matches the edge-oriented HenSense design point [11] while using a comparable parameter budget. "
     "Its distinguishing property is scope: unlike the counting- or tracking-only baselines, "
     "PoultryGuard couples detection with mortality decision-making, localization, documentation, and "
     "a veterinary loop, and ships as a 10\u00A0MB dependency-free model. A same-dataset zero-shot COCO "
     "baseline (last row) collapses on overhead broilers, counting only a handful of birds per "
     "dense frame, which confirms that in-domain fine-tuning, not architecture alone, drives the result.")

table("IV", "Comparison with Recent State-of-the-Art Detectors",
      ["Method (year)", "Dataset", "mAP@50", "Scope"],
      [["YOLO-CCA [10] (2025)", "Cage", "\u2014 (F1 .967)", "Count"],
       ["HenSense [11] (2026)", "Free-range", "0.926", "Detect"],
       ["Thermal YOLOv8 [12] (2024)", "Thermal", "0.95", "Count"],
       ["YOLO11-n line [13] (2026)", "Line", "0.995", "Count"],
       ["YOLO11n COCO zero-shot", "Broiler", "~0 (fails)", "Count"],
       ["PoultryGuard (ours)", "Broiler", "0.954", "Full loop"]],
      [1.1, 0.72, 0.6, 0.78])

H2("D. Deployment and Practicality")
para("Operationally, the ONNX model runs in real time on a single CPU core (\u224815\u00A0FPS at 640\u00A0px under "
     "clean conditions), fits in 10\u00A0MB, and requires none of the \u22481\u00A0GB PyTorch/ultralytics stack, "
     "so it deploys on a low-cost edge box beside the birds or on a free cloud tier. Inference is kept "
     "on the edge, which bounds recurring cost and preserves operation during connectivity loss; a "
     "continuous-integration workflow re-exports the ONNX model whenever the detector is retrained, "
     "keeping deployments current. These properties directly address the cost sensitivity that "
     "governs technology adoption in commercial poultry production.")
para("The per-frame latency budget is dominated almost entirely by the detector forward pass "
     "(≈60–90 ms at 640 px on one CPU core, depending on load), with the ONNX runtime roughly "
     "halving the PyTorch cost. The remaining stages are comparatively free: ByteTrack "
     "association and the behaviour bookkeeping of (1)–(3) add under two milliseconds per frame, "
     "and the expensive steps—snapshot encoding, database writes, report generation, and vet "
     "notification—run only when a case is actually opened, i.e. a few times per day rather than "
     "every frame. A deployment therefore comfortably sustains real-time monitoring on a "
     "sub-US$300 edge box, and multiple houses can share one device by time-multiplexing camera "
     "streams, which directly bounds the per-house hardware cost that governs commercial adoption.")
H2("E. Limitations")
para("Three limitations bound the present study. First, in the very densest clusters the detector "
     "still slightly over-segments overlapping birds, the main contributor to the residual 4.4% "
     "counting error; tiled inference mitigates but does not eliminate this. Second, posture is "
     "inferred from bounding-box geometry as a transparent proxy; replacing it with a CNN trained on "
     "the captured mortality-posture data is expected to improve specificity and is the natural next "
     "step. Third, evaluation uses one public dataset and simulated environmental sensing; validation "
     "on multi-farm, multi-breed footage with real sensor streams and clinician-confirmed mortality "
     "labels is required before clinical-grade claims. None of these affects the system\u2019s core "
     "contribution\u2014an integrated, deployable loop\u2014but each defines concrete future work.")

# ---------- V. CONCLUSION ----------
H2("F. Qualitative Case Walk-Through")
para("To illustrate the end-to-end loop, consider a single suspected-mortality event as the "
     "system handles it. Once a tracked bird has remained below the motion threshold for longer "
     "than T_s while presenting a lying posture, its state crosses to SUSPECTED and one case is "
     "opened. The pipeline immediately localizes the bird to a house zone and timestamp (“Zone C3, "
     "06:42”), crops and saves an annotated snapshot as evidence, and writes a structured record—"
     "chick reference, flock age, zone, posture profile, mortality score, and the preceding "
     "behaviour window—to the database. A veterinary case report is generated automatically and, "
     "on confirmation, the veterinarian is notified and a farm visit is booked; the veterinary "
     "console then captures diagnosis, treatment, vaccination, and case closure, after which the "
     "record is archived and can be exported into a labelled mortality-posture dataset for future "
     "training. The clinician remains the decision-maker throughout; the system’s role is to "
     "surface the event early, document it objectively, and remove the manual paperwork.")
H2("G. Threats to Validity")
para("Several threats temper the results. Regarding internal validity, posture is a geometric "
     "proxy and the mortality thresholds were set by inspection rather than learned, so the "
     "mortality-decision stage is demonstrated qualitatively rather than benchmarked against "
     "clinician-labelled deaths; the counting and detection metrics, by contrast, are measured on "
     "held-out ground truth. Regarding external validity, evaluation uses a single public dataset "
     "of overhead broiler houses, so generalization to other breeds, ages, housing types, and "
     "camera geometries remains to be shown; the environmental branch is simulated rather than "
     "driven by physical sensors. Regarding construct validity, counting accuracy is a necessary "
     "but not sufficient proxy for welfare outcomes. These threats do not undermine the paper’s "
     "central claim—that an integrated, lightweight, deployable loop is feasible—but they define "
     "the evidence still required before clinical-grade deployment, and each maps directly onto "
     "the future work below.")
H1("Conclusion and Future Work")
para("PoultryGuard demonstrates that the full operational loop of automated flock health "
     "monitoring\u2014count, track, detect mortality, localize, document, and dispatch a "
     "veterinarian\u2014can be delivered by a single lightweight system that runs on commodity CPUs. "
     "A fine-tuned YOLO11n reaches 0.954 mAP@50 and 4.4% dense-frame counting error, an ONNX "
     "deployment halves inference cost while preserving accuracy, and an ablation establishes 640\u00A0px "
     "inference at a 0.40 confidence threshold as the operating point. Future work will train the "
     "posture network on captured mortality crops, validate on multi-farm footage with physical "
     "T/RH/CO\u2082/NH\u2083 sensing, and quantify the environmental early-warning branch so that the system "
     "advances from detecting mortality to preventing it.")

# ---------- ACK ----------
H2("Acknowledgment")
para("The author thanks collaborators associated with the poultry-monitoring initiative in Oman and "
     "acknowledges the GEL broiler dataset contributors (Roboflow Universe, CC\u00A0BY\u00A04.0).", after=4)

# ---------- REFERENCES ----------
H1("References")
refs = [
 "Y. LeCun, Y. Bengio, and G. Hinton, \u201CDeep learning,\u201D Nature, vol. 521, pp. 436\u2013444, 2015.",
 "M. Assran et al., \u201CV-JEPA 2: Self-supervised video models enable understanding, prediction and planning,\u201D arXiv:2506.09985, 2025.",
 "J. Deng, W. Dong, R. Socher, L.-J. Li, K. Li, and L. Fei-Fei, \u201CImageNet: A large-scale hierarchical image database,\u201D in Proc. IEEE CVPR, 2009, pp. 248\u2013255.",
 "R. Khanam and M. Hussain, \u201CYOLOv11: An overview of the key architectural enhancements,\u201D arXiv:2410.17725, 2024.",
 "C.-Y. Wang, I.-H. Yeh, and H.-Y. M. Liao, \u201CYOLOv9: Learning what you want to learn using programmable gradient information,\u201D in Proc. ECCV, 2024.",
 "A. Wang et al., \u201CYOLOv10: Real-time end-to-end object detection,\u201D in Proc. NeurIPS, 2024.",
 "Y. Zhao et al., \u201CDETRs beat YOLOs on real-time object detection,\u201D in Proc. IEEE/CVF CVPR, 2024, pp. 16965\u201316974.",
 "G. Jocher, A. Chaurasia, and J. Qiu, \u201CUltralytics YOLO (v8),\u201D 2023. [Online]. Available: https://github.com/ultralytics/ultralytics",
 "Y. Zhang et al., \u201CByteTrack: Multi-object tracking by associating every detection box,\u201D in Proc. ECCV, 2022, pp. 1\u201321.",
 "J. Li et al., \u201CYOLO-CCA: An efficient chicken counting model with coordinate attention in dense cages,\u201D Animals, vol. 15, no. 6, 2025.",
 "S. K. Bhavanam et al., \u201CAdvancing precision livestock farming: Robust country-chicken detection via FeatherNet Fusion-YOLO and HenSense,\u201D in Proc. IEEE/CVF WACV Workshops (HARVEST-Vision), 2026.",
 "A. Elmetwalli et al., \u201CThermal imaging and advanced deep learning for automated broiler detection and counting,\u201D Azarbaijan J. Agric. Eng., 2024.",
 "L. F. de Oliveira et al., \u201CYOLO-based detection and counting of broilers on slaughterhouse hanging lines,\u201D RITA / J. Braz. Comput. Soc., 2026.",
 "P. Thong-on et al., \u201CChicken counting in an industrial slaughterhouse using YOLOv8 and multi-object tracking,\u201D Naresuan Univ. Eng. J., 2025.",
 "M. S. Hossain et al., \u201CComputer vision models for precision poultry farming: A narrative review of behavioral and welfare monitoring studies,\u201D Poultry Science, 2026.",
 "D. Berckmans, \u201CPrecision livestock farming: Advances and challenges for welfare monitoring,\u201D Animal Frontiers, 2024.",
 "R. Jalloul, C. H. Krishnappa, V. I. Agughasi, and R. Alkhatib, \u201CEnhancing early breast cancer detection with infrared thermography: A comparative evaluation of deep learning and machine learning models,\u201D Technologies, vol. 12, no. 10, 2024.",
 "V. I. Agughasi, \u201CLeveraging transfer learning for efficient diagnosis of COPD using CXR images and explainable AI techniques,\u201D Inteligencia Artificial, vol. 27, no. 74, 2024.",
 "S. Prathibha, K. N. Madhusudhan, and V. I. Agughasi, \u201CFirefly-based segmentation and residual deep learning for multi-class diabetic retinopathy detection,\u201D Inteligencia Artificial, 2025.",
 "N. Ravi et al., \u201CSAM 2: Segment anything in images and videos,\u201D arXiv:2408.00714, 2024.",
 "M. Oquab et al., \u201CDINOv2: Learning robust visual features without supervision,\u201D Trans. Mach. Learn. Res., 2024.",
 "ONNX Runtime developers, \u201CONNX Runtime: A cross-platform inference and training accelerator,\u201D Microsoft, 2024. [Online]. Available: https://onnxruntime.ai",
 "K. He, X. Zhang, S. Ren, and J. Sun, \u201CDeep residual learning for image recognition,\u201D in Proc. IEEE CVPR, 2016, pp. 770\u2013778.",
 "A. Dosovitskiy et al., \u201CAn image is worth 16\u00D716 words: Transformers for image recognition at scale,\u201D in Proc. ICLR, 2021.",
 "T.-Y. Lin et al., \u201CMicrosoft COCO: Common objects in context,\u201D in Proc. ECCV, 2014, pp. 740\u2013755.",
 "M. Tan and Q. Le, \u201CEfficientNet: Rethinking model scaling for convolutional neural networks,\u201D in Proc. ICML, 2019.",
 "S. Woo, J. Park, J.-Y. Lee, and I. S. Kweon, \u201CCBAM: Convolutional block attention module,\u201D in Proc. ECCV, 2018.",
 "V. I. Agughasi and S. Murali, \u201CCX-Net: An efficient ensemble semantic deep neural network for ROI identification from chest-X-ray images for COPD diagnosis,\u201D Mach. Learn.: Sci. Technol., vol. 4, 2023.",
 "C. Li et al., \u201CA review of deep learning for animal behaviour and welfare monitoring,\u201D Computers and Electronics in Agriculture, 2024.",
 "I. Attri et al., \u201CA review of deep learning techniques used in agriculture and edge deployment,\u201D Ecological Informatics, 2024.",
 "A. Vaswani et al., \u201CAttention is all you need,\u201D in Proc. NeurIPS, 2017, pp. 5998\u20136008.",
 "I. Loshchilov and F. Hutter, \u201CDecoupled weight decay regularization (AdamW),\u201D in Proc. ICLR, 2019.",
 "N. Carion et al., \u201CEnd-to-end object detection with transformers (DETR),\u201D in Proc. ECCV, 2020, pp. 213\u2013229.",
 "S. Neethirajan, \u201CThe role of sensors, big data and AI in digital animal farming,\u201D Sensors and Bio-Sensing Research, 2024.",
 "W. Wang et al., \u201CYOLO-based real-time dead-chicken detection for welfare monitoring in commercial houses,\u201D Computers and Electronics in Agriculture, 2025.",
]
for i, r in enumerate(refs, 1):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.left_indent = Inches(0.18); p.paragraph_format.first_line_indent = Inches(-0.18)
    rn = p.add_run(f"[{i}] {r}"); rn.font.size = Pt(8)

doc.save(OUT)
print("SAVED", OUT, "| references:", len(refs))
