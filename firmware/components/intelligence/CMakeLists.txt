# Intelligence Component
# Edge intelligence calculations: H_i, Q_i, R_i, baseline, anomaly, evidence, etc.
# Reference: reference/python/nexalert_reference/

idf_component_register(
    SRCS "health.c" "quality.c" "reliability.c" "baseline.c" "anomaly.c" "evidence.c" "confidence.c" "severity.c" "risk.c" "hazard_state.c"
    INCLUDE_DIRS "include"
    REQUIRES
)
