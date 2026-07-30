# Research Report: How do vaccines create immunity?

*Generated 2026-07-30 07:23 UTC*

## Executive Summary

- The adaptive immune system recognizes antigens through highly specific receptors: T cells use T cell receptors (TCRs) to recognize antigens presented by MHC molecules, while B cells use surface immunoglobulins (B cell receptors) that can bind free antigens.
- Vaccines introduce harmless antigens—either a weakened or inactivated form of the pathogen, a fragment of it, or a toxoid—into the body.
- The provided sources indicate that vaccines generate long-lasting immunological memory through the activation and persistence of B cells (producing antibodies) and T cells (helper and cytotoxic).

## Key Findings

### 1. How does the adaptive immune system recognize and respond to antigens?

**Confidence:** 🟡 Medium

The adaptive immune system recognizes antigens through highly specific receptors: T cells use T cell receptors (TCRs) to recognize antigens presented by MHC molecules, while B cells use surface immunoglobulins (B cell receptors) that can bind free antigens. Upon recognition, B cells differentiate into plasma cells that secrete antibodies, which neutralize pathogens or mark them for destruction; T cells coordinate responses (helper T cells) or directly kill infected cells (cytotoxic T cells). The system also generates memory cells after a primary response, enabling faster and stronger reactions upon re-exposure to the same antigen, which is the basis for vaccination.

### 2. How do vaccines introduce harmless antigens to stimulate an immune response?

**Confidence:** 🟡 Medium

Vaccines introduce harmless antigens—either a weakened or inactivated form of the pathogen, a fragment of it, or a toxoid—into the body. These antigens stimulate the adaptive immune system to produce specific antibodies and generate memory cells, without causing the actual disease. If the same pathogen is encountered later, the immune system mounts a faster and stronger response due to the pre-existing memory cells.

**⚠️ Conflicting information detected:**
- One web snippet states: 'These antigens stimulate an immune response without causing the disease. They rely on antibiotics to stimulate immunity.' This contradicts other sources that clearly state the immune response is triggered by the antigens themselves, not antibiotics. Resolution: The snippet appears to come from a multiple-choice question where the statement about antibiotics is part of an incorrect answer choice; the correct answer (option B) is that antigens stimulate immunity, aligning with the other sources.

### 3. What mechanisms cause vaccines to generate long-lasting immunological memory via B and T cells?

**Confidence:** 🟠 Low

The provided sources indicate that vaccines generate long-lasting immunological memory through the activation and persistence of B cells (producing antibodies) and T cells (helper and cytotoxic). However, none of the excerpts detail the specific cellular or molecular mechanisms (e.g., germinal center reactions, memory cell differentiation, or homeostatic maintenance) by which this memory is established and maintained. The sources focus on general statements about vaccine types (live attenuated, toxoid, subunit) and route-dependent differences (e.g., intradermal BCG failing to produce lung memory), rather than explaining the underlying mechanisms.

**⚠️ Conflicting information detected:**
- One PDF states that 'live attenuated, toxoid, and subunit vaccines are key for inducing long-term immunity,' while a BCG vaccination source reports that intradermal BCG (a live attenuated vaccine) 'fails to generate long-lasting immunological memory in the lungs.' Resolution: The apparent conflict arises from different contexts—the first statement is a general classification, while the second specifically addresses a particular vaccine and route (intradermal BCG for pulmonary tuberculosis), which may explain the discrepancy. This is not a direct contradiction of mechanisms but of specific vaccine efficacy.

## Source Provenance

| Sub-question | Source | Status | URL |
|---|---|---|---|
| How does the adaptive immune system recognize and ... | wikipedia | ✅ valid | https://en.wikipedia.org/wiki/Adaptive_immune_system |
| How does the adaptive immune system recognize and ... | web_search | ✅ valid | https://courses.lumenlearning.com/odessa-biology2/chapter/adaptive-immune-response/ |
| How does the adaptive immune system recognize and ... | arxiv | ✅ valid | http://arxiv.org/abs/1004.2854v1 |
| How do vaccines introduce harmless antigens to sti... | wikipedia | ✅ valid | https://en.wikipedia.org/wiki/Adaptive_immune_system |
| How do vaccines introduce harmless antigens to sti... | web_search | ✅ valid | https://brainly.com/question/16651078 |
| How do vaccines introduce harmless antigens to sti... | arxiv | ✅ valid | http://arxiv.org/abs/1004.2854v1 |
| What mechanisms cause vaccines to generate long-la... | wikipedia | ✅ valid | https://en.wikipedia.org/wiki/Attenuated_vaccine |
| What mechanisms cause vaccines to generate long-la... | web_search | ✅ valid | https://www.academia.edu/92348583/Immunological_memory_as_the_fundamentals_of_vaccines |
| What mechanisms cause vaccines to generate long-la... | arxiv | ❌ invalid | http://arxiv.org/abs/1411.4413v2 |

## Overall Confidence Rating

🟡 Medium — reasonable coverage, but some sub-questions had limited or conflicting data.

## Pipeline Log

<details>
<summary>Click to expand full pipeline execution log</summary>

```
[2026-07-30T07:22:29.769283+00:00] === Starting pipeline for: How do vaccines create immunity? ===
[2026-07-30T07:22:34.140229+00:00] Parsed into 3 sub-questions.
[2026-07-30T07:22:34.140501+00:00] Fetching 'How does the adaptive immune system recognize and respond to antigens?' from wikipedia...
[2026-07-30T07:22:36.388851+00:00]   -> wikipedia: VALID (329 chars)
[2026-07-30T07:22:36.388941+00:00] Fetching 'How does the adaptive immune system recognize and respond to antigens?' from web_search...
[2026-07-30T07:22:39.779337+00:00]   -> web_search: VALID (1485 chars)
[2026-07-30T07:22:39.779453+00:00] Fetching 'How does the adaptive immune system recognize and respond to antigens?' from arxiv...
[2026-07-30T07:22:41.501510+00:00]   -> arxiv: VALID (3393 chars)
[2026-07-30T07:22:41.501650+00:00] Sub-query 'How does the adaptive immune system recognize and respond to antigens?' complete: 3/3 sources valid.
[2026-07-30T07:22:41.501731+00:00] Synthesizing 'How does the adaptive immune system recognize and respond to antigens?'...
[2026-07-30T07:22:46.217930+00:00]   -> Confidence: medium, Conflicts found: 0
[2026-07-30T07:22:46.218087+00:00] Fetching 'How do vaccines introduce harmless antigens to stimulate an immune response?' from wikipedia...
[2026-07-30T07:22:49.802840+00:00]   -> wikipedia: VALID (329 chars)
[2026-07-30T07:22:49.802937+00:00] Fetching 'How do vaccines introduce harmless antigens to stimulate an immune response?' from web_search...
[2026-07-30T07:22:53.309091+00:00]   -> web_search: VALID (1537 chars)
[2026-07-30T07:22:53.309165+00:00] Fetching 'How do vaccines introduce harmless antigens to stimulate an immune response?' from arxiv...
[2026-07-30T07:22:54.799408+00:00]   -> arxiv: VALID (2432 chars)
[2026-07-30T07:22:54.799745+00:00] Sub-query 'How do vaccines introduce harmless antigens to stimulate an immune response?' complete: 3/3 sources valid.
[2026-07-30T07:22:54.799867+00:00] Synthesizing 'How do vaccines introduce harmless antigens to stimulate an immune response?'...
[2026-07-30T07:23:02.806764+00:00]   -> Confidence: medium, Conflicts found: 1
[2026-07-30T07:23:02.806890+00:00] Fetching 'What mechanisms cause vaccines to generate long-lasting immunological memory via B and T cells?' from wikipedia...
[2026-07-30T07:23:04.856818+00:00]   -> wikipedia: VALID (280 chars)
[2026-07-30T07:23:04.856954+00:00] Fetching 'What mechanisms cause vaccines to generate long-lasting immunological memory via B and T cells?' from web_search...
[2026-07-30T07:23:07.519995+00:00]   -> web_search: VALID (1437 chars)
[2026-07-30T07:23:07.520068+00:00] Fetching 'What mechanisms cause vaccines to generate long-lasting immunological memory via B and T cells?' from arxiv...
[2026-07-30T07:23:10.527224+00:00]   -> arxiv: INVALID — Content did not overlap meaningfully with the sub-query (relevance check failed)
[2026-07-30T07:23:10.527345+00:00] Sub-query 'What mechanisms cause vaccines to generate long-lasting immunological memory via B and T cells?' complete: 2/3 sources valid.
[2026-07-30T07:23:10.527463+00:00] Synthesizing 'What mechanisms cause vaccines to generate long-lasting immunological memory via B and T cells?'...
[2026-07-30T07:23:17.695866+00:00]   -> Confidence: low, Conflicts found: 1
[2026-07-30T07:23:17.696016+00:00] === Pipeline run complete ===
```
</details>
