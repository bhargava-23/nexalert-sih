__NEXALERT__

__FIRE SPREAD, GEOSPATIAL SIMULATION, AFFECTED AREA & RISK/HEATMAP__

Final V1 Engineering Specification — Physical Model, Geometry, Risk & Visualization Contract

__Document role  
__This is the definitive V1 engineering specification for NexAlert's fire\-spread and geospatial chain\. It specifies how ignition becomes a spatially evolving arrival\-time field, how the field becomes current/warning/projected geometry, how physical footprint is separated from policy safety buffers, how the hazard risk surface is computed, and how all geospatial outputs are validated and exposed to downstream systems\.

__Field__

__Value__

Product

NexAlert

Problem

SIH26178 — resilient AI\-powered environmental monitoring and early warning

Document

05 — Fire Spread, Geospatial Simulation, Affected Area & Risk/Heatmap

Status

FINAL V1 IMPLEMENTATION BASELINE

Hero hazard

Forest fire

Primary compute

Raspberry Pi Master and/or cloud/backend

Edge restriction

Heavy raster/geospatial fire simulation MUST NOT run on ESP32

Model family

Rothermel\-family reduced directional ROS \+ arrival\-time / minimum\-travel\-time style propagation

Primary spatial source of truth

Arrival\-time field

__Honesty boundary  
__V1 is a physics\-informed engineering model derived from the Rothermel family, not a full operational wildfire simulator\. Simplified fuel classes, moisture proxying, reduced wind treatment and finite grid resolution are deliberate V1 assumptions\. They must be disclosed wherever relevant and must never be presented as full operational Rothermel/FARSITE fidelity\.

# Document Control & Authority

__Status__

__Meaning__

LOCKED

Algorithmic or architectural structure that implementation must preserve\.

PARAMETER

Numerical value requiring calibration, measurement, sensitivity testing or deliberate policy selection\.

ASSUMPTION

Explicit simplification used by V1; visible in metadata/UI when material\.

DEGRADED

A required input/capability is unavailable but a controlled fallback remains usable\.

UNKNOWN

There is insufficient information to produce a trustworthy output\.

ROADMAP

Potential future enhancement; outside V1\.

REJECTED

Approach intentionally excluded from V1\.

## Authority documents

__Topic__

__Primary source__

Overall system architecture

01 — Master Architecture & Invariants

Technical requirement

02 — TRD

Technology/runtime boundary

03 — Technology Stack / Deployment

Intelligence/hazard evidence

04 — Mathematical Intelligence & Hazard Reasoning

Hardware telemetry

06 — Hardware/Edge

Data provenance

08 — Data/Dataset

Dashboard rendering

13 — Authority Dashboard

Validation

17 — Validation

__Red\-team basis  
__The final adversarial fire/geospatial review confirmed the arrival\-time/event\-based approach, while requiring explicit handling of wind FROM→TO conversion, diagonal √2 distances, vector wind\+slope treatment, projected CRS, mid\-run environmental recomputation, MultiPolygon support, and footprint\-vs\-buffer semantics\. fileciteturn19file0 fileciteturn19file16

# 1\. Purpose & Design Goals

## 1\.1 What this engine does

The Fire/Geospatial Engine converts a validated fire incident plus environmental and geographic context into an evolving spatial model\. Its outputs are not merely a visual animation\. The engine produces an arrival\-time field that is then deterministically transformed into current physical footprint, warning/projection regions, a policy\-defined operational buffer, a spatial hazard\-risk index, and geometry/statistics for downstream exposure and response\.

## 1\.2 What it must prove

- Wind changes the direction and anisotropy of spread in a physically interpretable way\.
- Slope and aspect influence propagation direction and speed\.
- Different fuel classes produce different local spread behavior\.
- Moisture/context suppresses or allows spread\.
- Non\-burnable barriers block propagation and force the front around them\.
- Propagation is driven by computed arrival times, not a decorative expanding circle\.
- Current, warning and projected areas are derived from one source\-of\-truth arrival field\.
- The risk heatmap is distinct from physical footprint and exposure\.
- Environmental changes can update the future projection without rewriting elapsed history\.

## 1\.3 What it does NOT do

- No CFD/FIRETEC/WFDS\-class fluid/combustion simulation\.
- No ember spotting/reignition in V1\.
- No exact flame\-front turbulent physics\.
- No claim of operationally validated wildfire forecasting\.
- No hidden fabricated fuel, population, weather or infrastructure values\.
- No fire\-spread computation on the ESP32\.

# 2\. Canonical Terminology

__Term__

__Definition__

Cell

One element of the spatial simulation grid\.

Ignition point

Geographic point where the fire starts; mapped to a seed cell\.

Fuel cell

Grid cell with a configured fuel class/behavior\.

Burnable

Boolean/property indicating whether the cell can propagate fire in V1\.

ROS

Rate of spread, expressed as a distance per time under the model\.

Directional ROS

ROS for a specific propagation direction\.

Arrival time T\_a\(c\)

Earliest simulated time at which fire reaches cell c\.

Current footprint

Cells already reached by T\_a\(c\) <= now\.

Warning zone

Cells predicted to be reached within the short future horizon\.

Projection zone

Cells predicted to be reached within the longer future horizon\.

Physical footprint

Model\-derived fire area; a physics/model output\.

Operational buffer

Policy\-defined margin around the physical footprint; not physics\.

Hazard Risk Surface

Continuous operational index over space; not probability\.

Exposure

Population/infrastructure/citizen consequence associated with geometry; downstream concept\.

Simulation domain

Finite spatial region within which propagation is computed\.

__Naming rule  
__The UI and API must use 'physical footprint' when referring to arrival\-time\-derived fire geometry and 'operational buffer' when referring to a policy margin\. Never call a policy buffer 'the fire footprint\.'

# 3\. Input Contract

## 3\.1 Required input categories

__Input__

__Required__

__Source__

__Purpose__

Ignition point

YES

Incident/node location

Seed cell\.

Simulation CRS

YES

Configuration

Distance/area\-safe spatial operations\.

Grid/domain

YES

Configuration/geospatial preprocessing

Cell topology and extent\.

DEM / elevation

YES for claimed slope modeling

Preprocessed dataset

Slope/aspect\.

Fuel class

YES

Preprocessed configuration/raster

Base spread behavior\.

Fuel moisture/context

YES for moisture\-aware output

Environmental context / proxy

Moisture suppression\.

Wind speed

YES for wind\-aware output

Sensor/external context/configured assumption

Wind forcing\.

Wind direction

YES for directional wind

Sensor/external context/configured assumption

Propagation direction\.

Current time

YES

Simulation clock

Current footprint extraction\.

Projection horizons

YES

Configuration

Warning/projection extraction\.

## 3\.2 Optional/advanced inputs

- Higher\-resolution fuel behavior\.
- Live weather updates\.
- External observational evidence\.
- More detailed canopy/wind\-reduction information\.
- Additional infrastructure/context layers\.

## 3\.3 Canonical cell model

Cell  
  cell\_id  
  row  
  col  
  x  
  y  
  lat  
  lon  
  elevation\_m  
  slope\_rad  
  aspect\_rad  
  fuel\_model  
  fuel\_class  
  burnable  
  moisture\_index  
  base\_ros  
  arrival\_time\_s  
  state  
  ignition\_time\_s  
  burn\_time\_s  
  local\_ros\_features  
  local\_risk  


The backend may use a more optimized internal representation \(NumPy arrays, raster arrays, typed structs\) rather than this object layout\. The semantic fields remain canonical\.

# 4\. Coordinate Reference System & Spatial Units

## 4\.1 Non\-negotiable geospatial rule

__Never treat degrees as metres  
__Raw latitude/longitude is geographic angular coordinate data\. All grid spacing, distance, spread\-rate, buffering, polygon area and route geometry calculations that require metric units MUST use an appropriate projected CRS or an explicit geodesic method\.

## 4\.2 Recommended V1 strategy

Reproject the demo region into a local metric projected CRS suitable for the region \(for example, the correct UTM zone for the chosen demo location\)\. Keep WGS84 latitude/longitude for external identity and display, but use the projected coordinate system for simulation geometry and metric calculations\.

## 4\.3 Required transformations

Input:  
  WGS84 \(lat/lon\)  
      ↓  
Project to local metric CRS  
      ↓  
Build square simulation grid in metres  
      ↓  
Run spread / distance / buffer / area computations  
      ↓  
Polygon geometry in projected CRS  
      ↓  
Reproject to WGS84 for web map display  


## 4\.4 CRS metadata

__Field__

__Requirement__

crs\_id

Persist exact EPSG/CRS identifier\.

resolution\_m

Persist cell size\.

domain\_extent

Persist simulation bounds\.

transform

Persist/reconstruct raster transform\.

source\_crs

Persist original dataset CRS where relevant\.

The fire output metadata must state the CRS used for the simulation and the display transformation\.

# 5\. Terrain Engine — DEM, Slope & Aspect

## 5\.1 DEM

The terrain engine samples or resamples the chosen DEM onto the simulation grid\. The DEM value represents elevation in metres unless the source explicitly defines another unit and a conversion is performed\.

## 5\.2 Central\-difference gradient

__∂z/∂x = \(z\_E − z\_W\) / \(2Δx\)__

__∂z/∂y = \(z\_N − z\_S\) / \(2Δy\)__

__g = √\[\(∂z/∂x\)^2 \+ \(∂z/∂y\)^2\]__

__β = atan\(g\)__

Aspect is the uphill direction of the terrain gradient and is retained as a directional quantity for the slope vector\.

## 5\.3 Edge cells

__Case__

__Behavior__

Interior cell

Use two\-sided central differences\.

Domain edge

Use one\-sided difference or explicitly mark lower\-confidence terrain derivative\.

Missing elevation

Use configured flat\-terrain fallback only if enabled; mark TERRAIN\_DEGRADED\.

## 5\.4 Slope effect

The exact slope\-response function is a configurable Rothermel\-family reduction rather than a claim of full operational fidelity\. A simplistic linear approximation is acceptable only when documented and validated\. A steeper\-terrain response must be monotonic in the intended direction and must not create physically nonsensical negative or explosive rates\.

__Important  
__The V1 document does not invent a universal slope coefficient\. The selected function and coefficients belong in the parameter registry and must be sensitivity\-tested\. The red\-team review specifically warned that a pure linear slope factor can understate steep\-slope acceleration\. fileciteturn19file14

# 6\. Fuel Model

## 6\.1 V1 fuel representation

V1 uses a simplified categorical fuel scheme for the demo region\. It is explicitly not a full Anderson/Scott\-Burgan operational fuel\-model library\.

__Class__

__Conceptual behavior__

NON\_BURNABLE

ROS=0; fire cannot enter this cell\.

GRASS

Fast/low\-residence fuel behavior\.

SHRUB

Intermediate behavior\.

LIGHT\_FOREST

Moderate/variable spread\.

DENSE\_FOREST

Higher fuel load and context\-dependent spread\.

URBAN\_MIX

Configured cautiously; burnable status and behavior depend on the demo assumption\.

## 6\.2 Fuel profile

FuelProfile:  
  fuel\_model\_id  
  fuel\_class  
  base\_ros\_r0  
  wind\_response\_parameters  
  slope\_response\_parameters  
  moisture\_response\_parameters  
  burnable  
  provenance  
  calibration\_status  


## 6\.3 Provenance rule

Every demo fuel map must have an explicit source/provenance\. Hand\-labeled fuel classes are acceptable for a prototype, but the dashboard and documentation must identify them as simplified demo classification\.

# 7\. Moisture / Environmental Suppression

## 7\.1 V1 moisture model

The fire engine uses a normalized moisture index or equivalent environmental proxy to scale the base spread behavior\. Relative dryness should increase spread capability and wetter conditions should suppress it\.

__F\_M\(c\) ∈ \(0,1\]__

__ROS\_moisture\(c,d\) = ROS\_directional\(c,d\) × F\_M\(c\)__

## 7\.2 Proxy rule

__Do not equate humidity to fuel moisture  
__Relative humidity and rainfall are environmental proxies/context inputs\. They are not literally the same physical quantity as multi\-timelag fuel moisture\. V1 may use a calibrated proxy, but the implementation and UI must label it as a moisture proxy/simplification\.

## 7\.3 Example proxy structure

A configurable proxy can map recent humidity/rainfall/context into a normalized dryness/moisture index\. Exact coefficients must remain configurable and calibration\-driven\.

recent\_rain  
humidity\_context  
optional temperature\_context  
        ↓  
normalized moisture\_index  
        ↓  
moisture response F\_M ∈ \(0,1\]  


# 8\. Wind Model

## 8\.1 Wind direction convention

__Critical correctness rule  
__Meteorological wind direction is reported as FROM\. Fire propagation uses the reciprocal TO direction\.

__θ\_TO = \(θ\_FROM \+ 180°\) mod 360°__

This conversion MUST occur in the backend/fire model before the wind becomes a propagation vector\. The frontend must not compensate for a backend error\.

## 8\.2 Midflame wind

__U\_mid = WAF × U\_input__

__Term__

__Meaning__

U\_input

Input wind speed at the measurement/source height\.

WAF

Wind adjustment/reduction factor; configurable\.

U\_mid

Estimated wind speed relevant to fire\-spread formulation\.

The fixed reduction factor is a prototype simplification of more detailed canopy/vegetation adjustment\. If a more detailed method becomes available, it can replace the factor without changing the surrounding architecture\.

## 8\.3 Calm/missing wind

__Condition__

__Behavior__

U\_mid below configured calm threshold

Treat wind forcing as effectively zero and use near\-isotropic directional spread\.

Wind missing

Use only an explicitly configured calm\-wind/assumption path; label output DEGRADED\.

Wind stale

Do not silently treat as fresh; mark information degraded and use policy\-defined fallback\.

Wind direction invalid

Reject directional wind input; fall back only if configured and labeled\.

# 9\. Directional Wind \+ Slope Combination

## 9\.1 Design

Wind and slope are represented as directional influence vectors rather than independent arbitrary multipliers applied to each grid direction\. This reduces the number of free directional parameters and produces a coherent head\-fire direction when the forcings are aligned or opposed\.

## 9\.2 Vector convention

Use a local Cartesian coordinate system for the projected simulation grid\. Define \+x and \+y consistently with the projected coordinates\. Convert the TO wind bearing and uphill slope aspect into unit vectors in this coordinate frame\.

v\_hat\(θ\) = \[cos\(θ\_cartesian\), sin\(θ\_cartesian\)\]  
  
V\_w = M\_w\(U\_mid, fuel, context\) × v\_hat\(θ\_wind\_to\)  
V\_s = M\_s\(slope, fuel, context\) × v\_hat\(θ\_uphill\)  
  
V\_eff = V\_w \+ V\_s  
U\_eff = ||V\_eff||  
θ\_eff = atan2\(V\_eff\_y, V\_eff\_x\)  


## 9\.3 Resultant interpretation

__Output__

__Meaning__

U\_eff

Effective directional forcing strength used by the reduced directional model\.

θ\_eff

Preferred head\-fire direction under combined wind/slope forcing\.

Direction anisotropy

Degree to which spread differs by direction; determined by the approved directional/elliptical formulation\.

__Implementation note  
__The exact conversion from U\_eff to ellipse eccentricity and directional ROS belongs to the calibrated directional\-spread parameterization\. Do not hard\-code an unexplained linear 'eccentricity = wind × constant' relationship\. The model must be monotonic, bounded and validated\.

# 10\. Base & Directional Rate of Spread \(ROS\)

## 10\.1 Base ROS

Each burnable cell begins with a fuel\-specific baseline spread rate R0\(c\), representing the no\-wind/no\-slope reference under the configured reference moisture/context\.

__R\_base\(c\) = R0\(c\) × F\_M\(c\)__

## 10\.2 Directional response

The approved directional model maps the effective wind\+slope forcing and the candidate propagation bearing d into a directional multiplier/ROS\. For implementation, this should be represented by an explicit, testable function:

__ROS\(c,d\) = R\_base\(c\) × F\_dir\(c,d; V\_eff, θ\_eff, fuel\)__

F\_dir must be positive for burnable cells, equal to zero for non\-burnable cells, and must be bounded according to the calibrated profile\.

## 10\.3 Elliptical interpretation

The directional response is represented as an ellipse\-like anisotropic spread around the head\-fire direction\. The ellipse is a model representation of directional ROS, not a decorative shape drawn independently of the propagation\.

For each candidate bearing d:  
  angular\_offset = normalized\_angle\(d \- θ\_eff\)  
  directional\_factor = EllipseDirectionalFactor\(  
      angular\_offset,  
      eccentricity,  
      calibrated parameters  
  \)  
  ROS\(c,d\) = R\_base\(c\) × directional\_factor  


## 10\.4 No independent per\-neighbor hand tuning

__Rejected implementation  
__Do not create eight unrelated multipliers such as north×1\.0, northeast×1\.2, east×0\.9, etc\. without a physical/directional parameterization\. Directional differences must emerge from the common vector/ellipse formulation and cell\-specific inputs\.

# 11\. Simulation Grid & Neighborhood

## 11\.1 Grid

The simulation uses a regular 2D grid in projected metric coordinates\.

__Property__

__V1 rule__

Grid shape

Rectangular raster grid\.

Neighbourhood

8\-neighbor topology\.

Orthogonal distance

Δ\.

Diagonal distance

Δ√2\.

Cell coordinate

Projected x/y plus row/col index\.

__d\(c,n\) = Δ, if orthogonal;  Δ√2, if diagonal__

__Critical test  
__Using Δ for diagonal neighbors is a correctness bug\. It overestimates diagonal spread by √2 and can produce diamond/star artifacts in calm\-wind uniform tests\. fileciteturn19file1

# 12\. Arrival\-Time Propagation

## 12\.1 Source of truth

The primary output of the spread simulation is an arrival\-time field T\_a\(c\), not a frame\-by\-frame animation state\. Any visualization of the fire front must be derived from this field\.

## 12\.2 Initialization

For all cells c:  
  T\_a\(c\) = \+∞  
  state\(c\) = UNBURNED  
  
Map ignition point to seed cell s:  
  T\_a\(s\) = t0  
  state\(s\) = IGNITED  


## 12\.3 Candidate arrival

__T\_candidate\(n\) = T\_a\(c\) \+ d\(c,n\) / ROS\(c,d\)__

__T\_a\(n\) = min\[T\_a\(n\), T\_candidate\(n\)\]__

The direction d is the bearing from cell c to neighbour n in the model's coordinate convention\.

## 12\.4 Priority queue

Use a min\-priority queue keyed by the current best arrival time\. This produces event\-based propagation without requiring a tiny fixed simulation timestep\. It is appropriate for the SIH prototype because the output is a minimum\-travel\-time/arrival field rather than a full transient combustion PDE\.

push\(seed, T\_a\(seed\)\)  
  
while queue not empty:  
    c = pop\_min\(\)  
    if popped\_time > T\_a\(c\):  
        continue  
  
    for each neighbour n:  
        if outside\_domain: continue  
        if not burnable\(n\): continue  
        if already\_burned\_or\_frozen\(n\): continue  
  
        d = neighbor\_distance\(c,n\)  
        bearing = direction\(c,n\)  
        ros = compute\_ros\(c, bearing\)  
  
        if ros <= 0:  
            continue  
  
        candidate = T\_a\(c\) \+ d/ros  
  
        if candidate < T\_a\(n\):  
            T\_a\(n\) = candidate  
            parent\(n\) = c  
            push\(n, candidate\)  


## 12\.5 Cell state semantics

__State__

__Meaning__

UNBURNED

Arrival time not reached yet\.

IGNITED

Seed/current event initialization state\.

BURNING

Cell's arrival time is current/past and active under the run's semantic model\.

BURNED

Cell has passed through the active burn window; V1 does not support reignition\.

## 12\.6 No reignition

Once a cell has been treated as burned in a run, V1 does not model ember\-driven re\-ignition\. This is a documented scope boundary\.

# 13\. Current, Warning & Projection

## 13\.1 Current footprint

__A\_current\(t\) = \{ c | T\_a\(c\) ≤ t \}__

## 13\.2 Warning zone

__A\_warning\(t\) = \{ c | t < T\_a\(c\) ≤ t \+ τ\_w \}__

## 13\.3 Projection zone

__A\_projection\(t\) = \{ c | t < T\_a\(c\) ≤ t \+ τ\_p \}__

__τ\_p > τ\_w > 0__

Projection is conditional on the model assumptions remaining valid for the forecast horizon\. It must be labeled accordingly\.

## 13\.4 Nested geometry rule

__A\_current ⊆ A\_warning\_cumulative ∪ A\_current ⊆ A\_projection\_cumulative__

For UI clarity, the preferred dashboard representation is cumulative zones derived from arrival thresholds\. If the UI presents disjoint ring populations/areas, explicitly define those rings\. Never mix cumulative and disjoint semantics silently\.

## 13\.5 Replay

Replay uses the same arrival\-time field\. Moving the timeline changes the threshold t; it must not invoke a different rendering algorithm that disagrees with the field\.

# 14\. Changing Environmental Conditions During a Run

## 14\.1 Problem

A precomputed arrival\-time field assumes its environmental inputs remain valid over the modeled period\. If meaningful inputs change—especially wind direction/speed or other material forcing—the future field must be recomputed\.

## 14\.2 Mandatory recompute strategy

At update time t\_update:  
  1\. Freeze historical truth:  
       cells with T\_a\(c\) <= t\_update remain historical/current truth\.  
  2\. Extract current perimeter/frontier:  
       cells at or near the current boundary\.  
  3\. Apply new environmental/fuel/context inputs\.  
  4\. Reset future/unreached arrival times for affected domain\.  
  5\. Seed queue from current perimeter with arrival=t\_update  
       \(preserve elapsed history\)\.  
  6\. Recompute future propagation\.  
  7\. Generate a new projection version\.  
  8\. Record "projection updated" event\.  


__Important  
__Do not silently rewrite the past\. A dashboard should show that the future projection changed because model inputs changed\. The red\-team review explicitly requires recomputation from the current perimeter rather than patching an old field\. fileciteturn19file14

# 15\. Non\-Burnable Cells & Barriers

## 15\.1 Rule

__if burnable\(c\) = false → ROS\(c,d\) = 0__

A non\-burnable cell is not merely painted as a firebreak\. It is excluded from propagation\. The event\-based algorithm naturally routes around it through reachable burnable neighbors\.

## 15\.2 Barrier examples

- Water body\.
- Configured non\-burnable land cover\.
- Explicit synthetic firebreak test strip\.
- Map\-domain masked\-out area\.

## 15\.3 Ignition on non\-burnable cell

An ignition point mapping to a non\-burnable cell is an invalid simulation input and must be rejected/flagged rather than producing an empty or contradictory simulation\.

# 16\. Domain Boundaries & Missing Geodata

__Condition__

__Required behavior__

Fire reaches simulation edge

Clip geometry; display 'Projection clipped to simulation domain\.'

Ignition outside domain

Reject or require explicit domain expansion; do not silently clamp\.

Missing DEM

Optional flat\-terrain fallback only if configured; label TERRAIN\_DEGRADED\.

Missing fuel

Use only an explicit simplified/default fuel profile if configured; label assumption\.

Missing moisture

Use explicit default moisture profile only if configured; label assumption\.

Missing wind

Calm/assumed\-wind path only if configured; label DEGRADED\.

Invalid fuel value

Reject cell or map to explicit unknown/unusable class; never silently choose extreme fuel\.

Data extent mismatch

Clip/mark unavailable rather than extrapolate silently\.

# 17\. Affected\-Area Geometry Engine

## 17\.1 Raster\-to\-region

Arrival\-time raster  
   ↓  
threshold selection  
   ↓  
boolean cell mask  
   ↓  
connected\-component analysis  
   ↓  
raster/contour polygonization  
   ↓  
geometry validation  
   ↓  
optional display simplification  
   ↓  
GeoJSON / spatial DB representation  


## 17\.2 Geometry validity

Every derived polygon must be checked for validity\. Self\-intersections, ring defects and invalid topology must be repaired using a standard geometry\-validity operation where safe; if repair cannot produce a trustworthy result, flag the output rather than silently displaying corrupted geometry\.

## 17\.3 MultiPolygon

The output type must support Polygon and MultiPolygon from the beginning\. Disconnected burnable regions, barriers, masked domains and multiple future reachable components can produce multiple regions\.

## 17\.4 Simplification

Display\-only simplification MAY be applied to reduce web payload and visual noise\. The unsimplified raster/derived geometry remains the source for scientific/statistical calculations\.

## 17\.5 Geometry versioning

__Field__

__Purpose__

geometry\_version

Identify regeneration after model/input changes\.

source\_arrival\_run\_id

Tie geometry to arrival\-field computation\.

generated\_at

Trace when geometry was produced\.

model\_assumptions\_hash

Identify relevant parameter/input configuration\.

# 18\. Physical Footprint vs Operational Buffer

## 18\.1 Physical footprint

The physical footprint is derived from the arrival\-time field\. It answers: where does the modeled fire reach under the current model assumptions?

## 18\.2 Operational buffer

__B\_operational = buffer\(A\_physical, m\_policy\)__

m\_policy is a policy\-defined safety margin\. The buffer may be larger than the modeled footprint to account for operational caution, uncertainty or response policy\.

__Non\-negotiable distinction  
__The operational buffer is not a more accurate fire physics model\. It is a policy margin\. The dashboard must use separate labels, styles and layer semantics for footprint versus buffer\.

## 18\.3 Reprojection/buffer rule

Buffer distances must be calculated in the appropriate metric projected CRS\. Never apply a metre buffer directly to WGS84 degrees\.

# 19\. Hazard Risk Surface / Heatmap

## 19\.1 Purpose

The hazard risk surface expresses spatial urgency and operational concern\. It is not the physical footprint and it is not probability\.

## 19\.2 Spatial components

__U\_c = exp\(−λ\_τ τ\_c\)__

For cells already reached, set U\_c=1\. For unreachable/invalid future cells, handle according to domain policy rather than inventing a large finite arrival time\.

__R\_haz,c = w\_U U\_c \+ w\_I I\_c \+ w\_E E\_c__

__w\_U \+ w\_I \+ w\_E = 1__

__Component__

__Meaning__

U\_c

Time\-to\-arrival urgency; closer imminent arrival produces larger value\.

I\_c

Local hazard intensity/spread\-strength proxy, normalized within configured bounds\.

E\_c

Local escalation/trend contribution where a valid temporal field exists\.

## 19\.3 Intensity input

For V1 fire, I\_c may be derived from local normalized directional ROS or another approved local intensity proxy\. It must be normalized before combination\.

## 19\.4 Operational index label

__Display semantics  
__Call this 'Hazard Risk Surface', 'Spread Urgency Index' or equivalent\. Do not label it 'probability of fire' unless a separate statistical calibration process has established that interpretation\.

## 19\.5 Exposure separation

Population density, school count, hospital presence and infrastructure consequence are not direct ingredients of the physical hazard risk surface\. They belong to exposure/impact\. This prevents double counting the same consequence information in both spatial hazard intensity and exposure\.

# 20\. Risk Classification & Map Layers

## 20\.1 Continuous vs discrete

__Output__

__Representation__

Physical footprint

Discrete polygon\(s\) derived from arrival\-time threshold\.

Operational buffer

Distinct polygon\(s\) derived from physical footprint \+ policy margin\.

Warning/projection

Discrete polygon\(s\) derived from arrival\-time thresholds\.

Hazard risk

Continuous raster/heatmap\.

Exposure

Separate spatial/statistical layers\.

## 20\.2 Risk bands

Risk classification thresholds are configurable parameters\. Example labels may be LOW, MODERATE, ELEVATED, HIGH and CRITICAL\. The numeric cutoffs must be held in the parameter registry and validated for monotonic behavior\.

## 20\.3 Multi\-hazard rule

__Permanent rule  
__Fire risk, flood risk, pollution risk and other hazard risk surfaces remain separate and independently toggleable\. Do not algebraically add or average unrelated hazard surfaces into a single universal disaster\-risk number\. fileciteturn19file16

# 21\. Area, Growth & Spatial Statistics

## 21\.1 Area

Area is calculated from the valid projected geometry or an appropriate geodesic/equal\-area method\.

__A\(t\) = area\(PhysicalFootprint\(t\)\)__

## 21\.2 Area growth

__G\_A\(t\) = \[A\(t\) − A\(t−Δt\)\] / Δt__

The UI may display growth as m²/min, ha/min or another clearly labeled unit\.

## 21\.3 Mean spread rate

Where a scalar summary is required, define it explicitly as an aggregate diagnostic \(for example perimeter\-normal or area\-equivalent growth rate\) rather than confusing it with directional ROS\. Directional ROS and footprint growth are different quantities\.

## 21\.4 Do not conflate

__Quantity__

__Meaning__

ROS

Local directional propagation rate\.

Arrival time

Time required to reach a cell\.

Area

Area already reached by a chosen threshold\.

Area growth

Rate of area change over time\.

Risk surface

Operational spatial index\.

# 22\. Downstream Exposure Interface

## 22\.1 What this engine provides

GeospatialOutput  
  incident\_id  
  run\_id  
  crs  
  current\_geometry  
  warning\_geometry  
  projection\_geometry  
  operational\_buffer\_geometry  
  arrival\_time\_source  
  risk\_surface\_source  
  generated\_at  
  assumptions  
  domain\_extent  
  projection\_horizon  


## 22\.2 Exposure engine responsibilities

Population and infrastructure calculations are handled by the Exposure module\. This document only defines the geometry and spatial artifacts that it consumes\.

## 22\.3 Population semantics

Downstream exposure must choose either cumulative zone semantics or disjoint ring semantics and document the choice\. It must never naively add nested current/warning/projection populations\. fileciteturn19file13

# 23\. LIVE vs SIMULATION

## 23\.1 Same engine

The Fire Spread Engine is identical in LIVE and SIMULATION modes\. Only the source and control of environmental input values may differ\.

__Mode__

__Input source__

LIVE

Validated incident \+ current environmental/geospatial context\.

SIMULATION

Scenario\-controlled telemetry/environmental inputs marked SIMULATION\.

## 23\.2 Simulation rule

Synthetic telemetry reaches the same ingestion and intelligence path before a fire incident is created\. The fire engine receives the resulting structured hazard context just like a live incident\.

## 23\.3 Visualization rule

__No fake spread animation  
__The frontend must animate the same arrival\-time solution produced by this engine\. It must not draw an independent expanding circle, ellipse, or hand\-authored polygon just to look smoother\.

# 24\. Frontend / Dashboard Geospatial Contract

## 24\.1 Map objects

__Object__

__Source__

Current footprint

Physical arrival\-time\-derived geometry\.

Warning zone

Short\-horizon arrival threshold\.

Projection

Longer\-horizon arrival threshold\.

Operational buffer

Policy buffer around physical footprint\.

Risk heatmap

Hazard Risk Surface raster/source\.

Wind vector

Current wind TO direction \+ speed\.

Head\-fire direction

θ\_eff / derived model direction\.

Terrain

DEM/slope analytical layer where enabled\.

Fuel

Fuel\-class context layer where enabled\.

Nodes

Node registry\.

SOS

SOS store\.

Population/infrastructure

Exposure data\.

## 24\.2 Required map semantics

- Current footprint and operational buffer must be visually distinguishable\.
- Warning and projection must be labeled with time horizon\.
- Risk heatmap must not be mistaken for exact physical geometry\.
- Projection must be marked conditional on current/model assumptions\.
- Stale/degraded environmental inputs must be visible\.
- Map controls must allow independent toggling of each major layer\.

## 24\.3 Fire Spread page

The Fire Spread page must expose LIVE/SIMULATION state, play/pause/reset, time slider, current footprint, projection, risk layer, wind/environment context, and model assumptions\. The dashboard may show advanced technical data, but must obtain them from this backend output rather than recomputing them\.

# 25\. Failure & Edge\-Case Matrix

__Condition__

__Expected behavior__

Calm wind

Near\-isotropic spread; no division/degenerate ellipse errors\.

Missing wind

Explicit DEGRADED / calm\-wind assumption\.

Stale wind

Information degraded; projection updated or constrained\.

Wind from 0/90/180/270

Direction conversion tested; footprint rotates correctly\.

Wind \+ slope aligned

Faster preferred spread in aligned direction\.

Wind \+ slope opposed

Resultant direction reflects opposition; no sign errors\.

Cross\-slope wind

Resultant rotates between forcings rather than choosing one independently\.

Uniform fuel, flat, calm

Near\-circular spread with no grid\-artifact star/diamond\.

Different adjacent fuels

Different local spread response visible\.

Non\-burnable barrier

Fire routes around; never through barrier\.

Ignition on non\-burnable

Reject/flag\.

Missing DEM

Explicit flat\-terrain assumption or UNKNOWN\.

Unknown fuel

Explicit default/unknown behavior; no silent extreme class\.

Domain boundary reached

Clip and label domain limitation\.

Disconnected burnable islands

MultiPolygon output supported\.

Self\-intersecting derived polygon

Attempt validity repair; otherwise flag\.

Environmental change mid\-run

Recompute from current perimeter; preserve historical elapsed field\.

High ROS

No fixed\-timestep instability expected, but queue/runtime benchmark must be measured\.

No population data

Exposure unavailable; fire geometry still valid\.

# 26\. Mathematical & Geospatial Acceptance Tests

__ID__

__Test__

__Pass condition__

GEO\-001

Wind FROM→TO

Set wind FROM north and verify preferred fire propagation is southward \(TO\)\.

GEO\-002

Wind rotation

Rotate wind input by 90° in a uniform landscape; major spread axis rotates correspondingly\.

GEO\-003

Calm circularity

Uniform flat fuel \+ calm wind produces near\-circular spread\.

GEO\-004

Diagonal distance

Verify diagonal step uses Δ√2\.

GEO\-005

Barrier routing

Insert a non\-burnable strip; fire routes around it\.

GEO\-006

Fuel heterogeneity

Adjacent fuel classes create different local spread rates\.

GEO\-007

Moisture response

Increase moisture index while holding others fixed; spread decreases monotonically\.

GEO\-008

Slope response

Increase slope in controlled direction; spread response follows calibrated monotonic slope function\.

GEO\-009

Wind\+slope vector

Apply orthogonal wind/slope forcings; preferred direction reflects vector resultant\.

GEO\-010

Opposing forcings

Apply opposing wind/slope vectors; no sign reversal or NaN\.

GEO\-011

Arrival ordering

Known small grid produces increasing arrival times along valid propagation path\.

GEO\-012

Footprint extraction

At time t, footprint equals cells with T\_a <= t\.

GEO\-013

Projection extraction

Projection equals configured future threshold on same T\_a field\.

GEO\-014

Replay consistency

Changing time cursor produces same geometry as recomputing threshold on stored T\_a\.

GEO\-015

Mid\-run recompute

Change wind; future projection changes while historical state stays unchanged\.

GEO\-016

Boundary clip

Fire reaching domain edge yields clipped geometry with explicit label\.

GEO\-017

MultiPolygon

Disconnected burnable regions yield MultiPolygon where appropriate\.

GEO\-018

Polygon validity

All displayed output geometries pass validity test\.

GEO\-019

Projected CRS

Known metric test passes for distance/area/buffer\.

GEO\-020

Buffer separation

Operational buffer differs geometrically and semantically from physical footprint\.

GEO\-021

Risk monotonicity

Earlier arrival, all else fixed, does not reduce urgency term\.

GEO\-022

Risk independence

Population overlay does not change physical hazard risk surface\.

GEO\-023

No risk aggregation

Fire and flood surfaces remain separate outputs\.

GEO\-024

Missing wind labeling

Withhold wind and verify explicit degraded assumption\.

GEO\-025

No silent fabricated data

Missing fuel/population/infrastructure never becomes an unlabelled numeric value\.

# 27\. Calibration & Validation Strategy

## 27\.1 Fire sensing vs fire spread

Sensor validation and fire\-spread validation are related but distinct\. Real controlled fire trials primarily calibrate the sensing/evidence pathway\. Geospatial spread behavior is validated with controlled synthetic or empirical benchmark scenarios plus sensitivity tests\.

## 27\.2 Calibration sequence

1. Lock final fuel class map and provenance for the demo region\.
2. Establish baseline R0 values/behavior from declared sources or controlled calibration assumptions\.
3. Establish moisture response calibration/parameter ranges\.
4. Validate wind direction and speed response independently\.
5. Validate slope response independently\.
6. Validate combined wind\+slope behavior\.
7. Validate heterogeneous fuel behavior\.
8. Validate barriers and geometry\.
9. Benchmark runtime on the actual Master/cloud target\.

## 27\.3 No pseudo\-accuracy

Do not report a single 'fire spread accuracy = 94%' unless a scientifically appropriate validation protocol and reference observations support that statement\. For SIH, report model assumptions, sensitivity tests, controlled validation observations, and measured runtime\.

## 27\.4 Reference\-image/video visual quality

The physics engine and visualization polish are separate acceptance dimensions\. A smooth UI cannot compensate for incorrect physics, and correct physics can be visually polished independently\. Any reference video comparison must therefore be assessed on \(a\) physical behavior, \(b\) geospatial geometry, \(c\) temporal evolution, and \(d\) rendering quality\.

# 28\. Performance & Runtime

## 28\.1 Compute target

The spread engine runs on Raspberry Pi/cloud\-class compute, not on ESP32\. The first benchmark target is the actual Raspberry Pi hardware intended for the demo\.

## 28\.2 Metrics

__Metric__

__Definition__

Grid size

Rows × columns\.

Cells evaluated

Number of cells popped/relaxed or otherwise processed\.

Queue operations

Push/pop count\.

Wall time

Simulation runtime\.

Memory peak

Maximum RAM used by raster/queue/geometry\.

Polygonization time

Time from mask to valid geometry\.

Risk surface time

Time to compute hazard risk raster\.

End\-to\-end update

Incident update to dashboard render\.

## 28\.3 Performance optimization order

- Use efficient numeric arrays rather than Python object\-per\-cell loops where possible\.
- Keep priority queue implementation efficient\.
- Limit simulation domain to required geospatial extent\.
- Avoid recomputing immutable terrain/fuel preprocessing on every update\.
- Cache DEM/fuel transforms and display\-ready data\.
- Regenerate future wavefront only when material input changes\.
- Optimize polygonization only after correctness is proven\.

# 29\. Storage & Provenance

## 29\.1 Required persisted metadata

__Artifact__

__Persist__

Spread run

incident\_id, run\_id, timestamps, mode, parameter\-set ID, domain, CRS\.

Environmental context

wind, moisture, temperature/context inputs used by run\.

Terrain

dataset ID/version, CRS, preprocessing version\.

Fuel

dataset/config ID, version/provenance, classification status\.

Arrival field

file/reference ID, transform, resolution, source run\.

Geometry

geometry version, source arrival run, generated timestamp\.

Risk surface

formula/config version, source arrival run\.

Assumptions

human\-readable list of fallbacks/limitations active during run\.

## 29\.2 Reproducibility

Given the same immutable inputs, configuration and model version, a spread run should be reproducible to the defined numerical tolerance\. Store enough metadata to reconstruct that condition\.

# 30\. Recommended Software Module Structure

geospatial/  
  fire\_spread/  
    domain\.py  
    grid\.py  
    wind\.py  
    terrain\.py  
    fuel\.py  
    moisture\.py  
    ros\.py  
    propagation\.py  
    arrival\_time\.py  
    recompute\.py  
  affected\_area/  
    thresholds\.py  
    polygonize\.py  
    geometry\_validity\.py  
    multipolygon\.py  
    buffers\.py  
  risk/  
    urgency\.py  
    intensity\.py  
    escalation\.py  
    surface\.py  
    classification\.py  
  datasets/  
    dem\.py  
    fuel\.py  
    population\.py  
    infrastructure\.py  
  io/  
    raster\_store\.py  
    geojson\.py  
    provenance\.py  
tests/  
  fire\_spread/  
  affected\_area/  
  risk/  
  fixtures/  


## 30\.1 Module ownership

__Module__

__Owns__

wind\.py

FROM→TO, wind vector, midflame adjustment\.

terrain\.py

DEM sampling, slope/aspect\.

fuel\.py

Fuel profiles/class lookup\.

moisture\.py

Moisture/context normalization\.

ros\.py

Base and directional ROS\.

propagation\.py

Priority queue / arrival\-time field\.

recompute\.py

Mid\-run environment updates\.

polygonize\.py

Raster\-to\-geometry\.

geometry\_validity\.py

Validity checks/repair\.

buffers\.py

Operational policy buffer\.

surface\.py

Hazard risk raster\.

classification\.py

Risk bands\.

# 31\. Service/API Contract

__Endpoint__

__Purpose__

GET /api/v1/incidents/\{id\}/spread

Current spread summary and geometry references\.

GET /api/v1/incidents/\{id\}/spread/run/\{run\_id\}

Detailed spread\-run metadata/output\.

GET /api/v1/incidents/\{id\}/spread/arrival

Arrival\-time source/tiles/reference where exposed\.

GET /api/v1/incidents/\{id\}/spread/risk

Hazard risk surface metadata/source\.

GET /api/v1/incidents/\{id\}/affected\-area

Current/warning/projection/buffer geometry\.

## 31\.1 Conceptual response

\{  
  "incident\_id": "INC\-FIRE\-0041",  
  "mode": "LIVE",  
  "run\_id": "RUN\-0017",  
  "updated\_at": "\.\.\.",  
  
  "environment": \{  
    "wind\_speed\_mps": 4\.8,  
    "wind\_from\_deg": 240,  
    "wind\_to\_deg": 60,  
    "moisture\_index": 0\.34  
  \},  
  
  "geometry": \{  
    "current": "GeoJSON/feature\-reference",  
    "warning": "GeoJSON/feature\-reference",  
    "projection": "GeoJSON/feature\-reference",  
    "operational\_buffer": "GeoJSON/feature\-reference"  
  \},  
  
  "metrics": \{  
    "current\_area\_m2": 18420,  
    "warning\_area\_m2": 27100,  
    "projection\_area\_m2": 39200,  
    "area\_growth\_m2\_per\_min": 510\.2  
  \},  
  
  "risk\_surface": \{  
    "kind": "HAZARD\_RISK\_INDEX",  
    "probability": false,  
    "source": "\.\.\."  
  \},  
  
  "assumptions": \[  
    "Simplified fuel classes",  
    "Projection assumes current environmental conditions until next update"  
  \]  
\}

# 32\. Simulation Scenarios

## 32\.1 Minimum scenario library

__Scenario__

__Purpose__

S01 Uniform calm

Geometry sanity; circle/diagonal test\.

S02 Wind rotation

Directional behavior\.

S03 Wind \+ slope

Combined vector behavior\.

S04 Fuel mosaic

Heterogeneous spread\.

S05 Firebreak

Barrier routing\.

S06 Moisture increase

Suppression response\.

S07 Rapid escalation

Response/update timing\.

S08 Wind shift mid\-run

Recompute future wavefront\.

S09 Domain edge

Boundary behavior\.

S10 Disconnected fuel islands

MultiPolygon\.

S11 Missing wind

Degraded assumption\.

S12 Missing DEM

Terrain degraded\.

S13 Invalid geometry

Repair/flag behavior\.

S14 Multi\-hazard context

Fire risk remains independent from other hazard risk\.

## 32\.2 Scenario metadata

Every scenario must identify which variables are held constant and which are changed\. This makes sensitivity tests interpretable\.

# 33\. SIH Demo Behavior

## 33\.1 Fire demo narrative

REAL EVENT  
  ↓  
ESP32 detects validated fire evidence  
  ↓  
Incident becomes CONFIRMED/CRITICAL  
  ↓  
Master starts Fire Spread Engine  
  ↓  
terrain \+ fuel \+ moisture \+ wind  
  ↓  
directional ROS  
  ↓  
arrival\-time field  
  ↓  
current footprint  
  ↓  
warning \+ projection  
  ↓  
risk heatmap  
  ↓  
affected population/infrastructure  
  ↓  
response recommendation  
  ↓  
authority dashboard \+ citizen alert  


## 33\.2 Technical judge interaction

The operator must be able to show the model rather than merely the animation: wind direction, terrain/fuel assumptions, current footprint, projection horizon, and the explanation that geometry is derived from the arrival\-time field\.

## 33\.3 LIVE→SIMULATION

After the live event, switch to SIMULATION\. A scenario generates telemetry through the standard ingestion path\. The same Fire Spread page then renders the resulting incident\. The fact that the screen and downstream outputs remain structurally identical is part of the proof that simulation is not a separate toy system\.

# 34\. Explicit V1 Non\-Goals

__Feature__

__Decision__

Full CFD / combustion physics

DO NOT BUILD\.

FIRETEC/WFDS\-class simulation

DO NOT BUILD\.

Ember spotting/reignition

DO NOT BUILD\.

Dynamic full atmospheric fluid field

DO NOT BUILD\.

Full 13/40 fuel\-model operational library

OUTSIDE V1; use simplified classified scheme\.

Full live satellite dependency

DEFERRED\.

3D globe/terrain

DO NOT BUILD for V1\.

Custom vector\-tile pipeline

DO NOT BUILD for demo scale\.

Pixel\-perfect imitation of a reference video without matching physics

DO NOT BUILD\.

# 35\. Fire/Geospatial Invariants

__🔒 01  __Fire spread is computed from an arrival\-time field, not a decorative animation\.

__🔒 02  __Meteorological wind FROM direction is converted to TO before propagation\.

__🔒 03  __Diagonal grid distance is Δ√2\.

__🔒 04  __Wind and slope are treated directionally through a common vector/resultant model\.

__🔒 05  __Base ROS, moisture response and directional response remain explicit and configurable\.

__🔒 06  __Non\-burnable cells have zero propagation and route the front around barriers\.

__🔒 07  __Physical footprint is arrival\-time\-derived\.

__🔒 08  __Operational buffer is a separate policy layer\.

__🔒 09  __Warning/projection are thresholded from the same arrival\-time field\.

__🔒 10  __Projection is conditional on stated assumptions\.

__🔒 11  __Environmental changes trigger recomputation from current perimeter for future propagation\.

__🔒 12  __Simulation and live use the same fire\-spread engine\.

__🔒 13  __Area/distance/buffer calculations use an appropriate metric CRS/geodesic method\.

__🔒 14  __Polygon outputs are validity\-checked\.

__🔒 15  __MultiPolygon is supported\.

__🔒 16  __Display simplification never changes scientific/source geometry\.

__🔒 17  __Risk heatmap is an operational index, not a probability\.

__🔒 18  __Population/infrastructure exposure does not redefine physical hazard risk\.

__🔒 19  __Fire and other hazard risk surfaces remain independently represented\.

__🔒 20  __Missing geodata produces explicit degraded/unknown behavior\.

__🔒 21  __Fire spread runs on Master/cloud compute, never on ESP32\.

__🔒 22  __Every run records parameter and data provenance sufficient for reproduction\.

# 36\. Implementation Readiness Checklist

__☐ 01  __Demo\-region CRS selected and persisted\.

__☐ 02  __DEM dataset selected, preprocessed and provenance recorded\.

__☐ 03  __Simplified fuel map created, versioned and labeled\.

__☐ 04  __Moisture proxy defined and parameterized\.

__☐ 05  __Wind source defined; FROM→TO verified in code\.

__☐ 06  __Midflame wind adjustment parameter exists\.

__☐ 07  __Directional wind\+slope vector model implemented\.

__☐ 08  __Directional ROS/ellipse function implemented and unit\-tested\.

__☐ 09  __8\-neighbor grid implemented with Δ and Δ√2 distances\.

__☐ 10  __Priority\-queue propagation implemented\.

__☐ 11  __Arrival\-time field persisted/recoverable\.

__☐ 12  __Current/warning/projection generated only from arrival field\.

__☐ 13  __Mid\-run environment recompute implemented\.

__☐ 14  __Non\-burnable routing tested\.

__☐ 15  __MultiPolygon supported\.

__☐ 16  __Geometry validity/repair implemented\.

__☐ 17  __Physical footprint and operational buffer are separate outputs\.

__☐ 18  __Hazard Risk Surface implemented separately from footprint/exposure\.

__☐ 19  __Risk surface clearly labeled non\-probabilistic\.

__☐ 20  __LIVE and SIMULATION use identical spread engine\.

__☐ 21  __Runtime benchmark completed on actual Master target\.

__☐ 22  __All mandatory GEO\-\* tests pass\.

# 37\. Source & Review Basis

This final specification incorporates the prior NexAlert fire/geospatial design and the adversarial review\. The review explicitly confirmed that the arrival\-time/event\-based approach is appropriate for the SIH scope, while identifying concrete corrections: wind FROM→TO conversion, diagonal √2 distance, vector wind\+slope combination, projected CRS, mid\-run future\-wavefront recomputation, MultiPolygon support, geometry validity repair, operational\-buffer separation, and independent hazard risk layers\. fileciteturn19file1 fileciteturn19file16

The dashboard reference further establishes that the Fire Spread page must render the same backend arrival\-time solution rather than inventing a separate visual animation, and that current/warning/projection plus risk/fuel/terrain overlays are derived from the model outputs\. fileciteturn19file2 fileciteturn19file13

The architecture baseline also establishes that external satellite data is additive/deferred rather than a dependency for minute\-scale local decisions, and that the V1 fire pathway is manually configured/calibrated rather than a trained classifier\. fileciteturn19file15

