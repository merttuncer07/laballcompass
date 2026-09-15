# V2P050 SCIG — Support-Covariance Independence Guard

SCIG composes R037 SACPS with CSID's safeguard portfolio engine. CSID already prevents same-label evidence families from being multiplied as if independent. SCIG targets the remaining failure: differently named evidence channels can still be common-mode. A support-aware covariance estimate can merge those channels into the same dependence component before CSID evaluates coverage and chooses a portfolio.

The removal control is the same CSID problem with covariance-based cross-family merging removed. The synthetic benchmark makes two nominally distinct feeds strongly dependent; label-only CSID chooses both, while SCIG detects the common-mode channel and selects a genuinely independent safeguard combination. If no supported cross-family dependence exists, SCIG collapses exactly to ordinary CSID. Near the declared correlation boundary it abstains.

Status: R388 shadow only. No canonical product/family count changes.
