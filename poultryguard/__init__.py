"""PoultryGuard - AI-Based Smart Poultry Health Monitoring, Mortality Detection
and Veterinary Response System (Proof of Concept).

Package layout
--------------
config      : runtime settings, thresholds, zone grid, target environment bands
detector    : YOLO wrapper (counting) with pluggable chicken weights
posture     : posture / body-condition classifier (geometry default, model-pluggable)
behavior    : per-track motion & behaviour history (speed, immobility, isolation)
mortality   : mortality state machine combining immobility + posture
zones       : frame -> zone id ("Zone B") localisation
sensors     : environmental sensor simulator + early-warning fusion
database    : SQLite persistence (cases, documentation, vet actions, sensor log)
reporting   : automatic veterinary case-report generation
vet         : vet notification / farm-visit booking (mock integration)
pipeline    : per-frame orchestrator tying everything together
draw        : annotation / overlay helpers
"""
__version__ = "0.1.0"
