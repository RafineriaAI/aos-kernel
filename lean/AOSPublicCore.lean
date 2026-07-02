import Std

inductive Verdict where
  | pass
  | warn
  | block
  deriving DecidableEq, Repr

inductive EvidenceLevel where
  | fixedOutputSmoke
  | fixedOutputHardCase
  | controlledStudyProtocolRun
  | controlledStudyProtocolReady
  deriving DecidableEq, Repr

inductive PublicEvidenceLevel where
  | insufficient
  | controlledStudyProtocol
  | controlledStudyEffectiveness
  deriving DecidableEq, Repr

def verdictRank : Verdict -> Nat
  | Verdict.pass => 0
  | Verdict.warn => 1
  | Verdict.block => 2


def intervalVerdict (upperBound limit warnMargin : Int) : Verdict :=
  if upperBound > limit then Verdict.block
  else if upperBound > limit - warnMargin then Verdict.warn
  else Verdict.pass

structure JsonGateInput where
  score : Int
  uncertainty : Int
  limit : Int
  warnMargin : Int
  metadataComplete : Bool
  deriving DecidableEq, Repr

structure AuditDecision where
  expected : Verdict
  observed : Verdict
  digestPresent : Bool
  replayed : Bool
  deriving DecidableEq, Repr

structure StudyCriteria where
  scenarioCount : Nat
  frozenModelOutputs : Bool
  datasetSourcesNamed : Bool
  sourceSplitsPresent : Bool
  modelOutputHashesValid : Bool
  sourceRecordHashesPresent : Bool
  recordIdsUnique : Bool
  outputGenerationMetadataPresent : Bool
  labelingProtocolPresent : Bool
  categoriesCovered : Bool
  difficultyD1D9Covered : Bool
  minimumCasesPerCategory : Bool
  minimumCasesPerDifficulty : Bool
  comparatorsNamed : Bool
  metricsPredefined : Bool
  caseLevelResultsIncluded : Bool
  scenarioHashIncluded : Bool
  replaySucceeded : Bool
  auditCoverageComplete : Bool
  deriving DecidableEq, Repr

structure EffectivenessCriteria where
  independentSignalExtraction : Bool
  labelsNotUsedAsSignals : Bool
  normalizationLayerEvaluated : Bool
  heldOutManualAuditPresent : Bool
  baselineInputsMatched : Bool
  failureCasesReported : Bool
  tradeoffMetricsReported : Bool
  deriving DecidableEq, Repr

def JsonGateInput.upperBound (input : JsonGateInput) : Int :=
  input.score + input.uncertainty

def auditDecisionReady (decision : AuditDecision) : Bool :=
  decision.digestPresent && decision.replayed

def silentBlockPassThrough (decision : AuditDecision) : Prop :=
  decision.expected = Verdict.block ∧ decision.observed = Verdict.pass

def studyDesignReady (criteria : StudyCriteria) : Bool :=
  decide (500 <= criteria.scenarioCount) &&
    criteria.frozenModelOutputs &&
    criteria.datasetSourcesNamed &&
    criteria.sourceSplitsPresent &&
    criteria.outputGenerationMetadataPresent &&
    criteria.labelingProtocolPresent &&
    criteria.categoriesCovered &&
    criteria.difficultyD1D9Covered &&
    criteria.minimumCasesPerCategory &&
    criteria.minimumCasesPerDifficulty &&
    criteria.comparatorsNamed &&
    criteria.metricsPredefined

def studyAuditReady (criteria : StudyCriteria) : Bool :=
  criteria.modelOutputHashesValid &&
    criteria.sourceRecordHashesPresent &&
    criteria.recordIdsUnique &&
    criteria.caseLevelResultsIncluded &&
    criteria.scenarioHashIncluded &&
    criteria.replaySucceeded &&
    criteria.auditCoverageComplete

def controlledStudyReady (criteria : StudyCriteria) : Bool :=
  studyDesignReady criteria && studyAuditReady criteria

def studyEvidenceLevel (criteria : StudyCriteria) : EvidenceLevel :=
  if controlledStudyReady criteria then
    EvidenceLevel.controlledStudyProtocolReady
  else
    EvidenceLevel.controlledStudyProtocolRun

def effectivenessReady (criteria : EffectivenessCriteria) : Bool :=
  criteria.independentSignalExtraction &&
    criteria.labelsNotUsedAsSignals &&
    criteria.normalizationLayerEvaluated &&
    criteria.heldOutManualAuditPresent &&
    criteria.baselineInputsMatched &&
    criteria.failureCasesReported &&
    criteria.tradeoffMetricsReported

def publicEvidenceLevel
    (criteria : StudyCriteria)
    (effectiveness : EffectivenessCriteria) : PublicEvidenceLevel :=
  if controlledStudyReady criteria then
    if effectivenessReady effectiveness then
      PublicEvidenceLevel.controlledStudyEffectiveness
    else
      PublicEvidenceLevel.controlledStudyProtocol
  else
    PublicEvidenceLevel.insufficient

def jsonInputWellFormed (input : JsonGateInput) : Prop :=
  0 <= input.score ∧
    0 <= input.uncertainty ∧
    0 <= input.limit ∧
    0 <= input.warnMargin ∧
    input.warnMargin < input.limit

def isValidInput (input : JsonGateInput) : Bool :=
  decide (0 <= input.score) &&
  decide (0 <= input.uncertainty) &&
  decide (0 <= input.limit) &&
  decide (0 <= input.warnMargin) &&
  decide (input.warnMargin < input.limit)

def jsonGateVerdict (input : JsonGateInput) : Verdict :=
  if input.metadataComplete && isValidInput input then
    intervalVerdict input.upperBound input.limit input.warnMargin
  else
    Verdict.block

theorem isValidInputTrueIffWellFormed
    (input : JsonGateInput) :
    isValidInput input = true ↔ jsonInputWellFormed input := by
  simp [isValidInput, jsonInputWellFormed, and_assoc]


theorem blockVerdictCorrect (upperBound limit warnMargin : Int) :
    upperBound > limit ->
    intervalVerdict upperBound limit warnMargin = Verdict.block := by
  intro h
  simp [intervalVerdict, h]

theorem passVerdictCorrect
    (upperBound limit warnMargin : Int) :
    0 <= warnMargin ->
    upperBound <= limit - warnMargin ->
    intervalVerdict upperBound limit warnMargin = Verdict.pass := by
  intro hMargin hPass
  have hNotBlock : Not (upperBound > limit) := by
    omega
  have hNotWarn : Not (upperBound > limit - warnMargin) := by
    omega
  simp [intervalVerdict, hNotBlock, hNotWarn]

theorem warnVerdictCorrect
    (upperBound limit warnMargin : Int) :
    upperBound > limit - warnMargin ->
    upperBound <= limit ->
    intervalVerdict upperBound limit warnMargin = Verdict.warn := by
  intro hWarn hNotBlock
  have hNoBlock : Not (upperBound > limit) := by
    omega
  simp [intervalVerdict, hNoBlock, hWarn]

theorem warnVerdictOnlyWithinBand
    (upperBound limit warnMargin : Int) :
    intervalVerdict upperBound limit warnMargin = Verdict.warn ->
    limit - warnMargin < upperBound /\ upperBound <= limit := by
  unfold intervalVerdict
  by_cases hBlock : upperBound > limit
  · simp [hBlock]
  · by_cases hWarn : upperBound > limit - warnMargin
    · intro _
      constructor <;> omega
    · simp [hBlock, hWarn]


theorem deterministicVerdict
    (upperBound limit warnMargin : Int) :
    Or
      (intervalVerdict upperBound limit warnMargin = Verdict.pass)
      (Or
        (intervalVerdict upperBound limit warnMargin = Verdict.warn)
        (intervalVerdict upperBound limit warnMargin = Verdict.block)) := by
  unfold intervalVerdict
  split
  · exact Or.inr (Or.inr rfl)
  · split
    · exact Or.inr (Or.inl rfl)
    · exact Or.inl rfl


theorem auditDecisionReadyHasDigest
    (decision : AuditDecision) :
    auditDecisionReady decision = true ->
    decision.digestPresent = true := by
  intro h
  simp [auditDecisionReady] at h
  exact h.1

theorem auditDecisionReadyHasReplay
    (decision : AuditDecision) :
    auditDecisionReady decision = true ->
    decision.replayed = true := by
  intro h
  simp [auditDecisionReady] at h
  exact h.2

theorem exactBlockDecisionNotSilent
    (decision : AuditDecision) :
    decision.expected = Verdict.block ->
    decision.observed = decision.expected ->
    Not (silentBlockPassThrough decision) := by
  intro hExpected hExact hSilent
  have hObservedBlock : decision.observed = Verdict.block := by
    rw [hExact, hExpected]
  have hObservedPass : decision.observed = Verdict.pass := hSilent.2
  rw [hObservedBlock] at hObservedPass
  contradiction

theorem controlledStudyAssessmentSound
    (criteria : StudyCriteria) :
    controlledStudyReady criteria = true ->
    studyEvidenceLevel criteria = EvidenceLevel.controlledStudyProtocolReady := by
  intro hReady
  simp [studyEvidenceLevel, hReady]

theorem controlledStudyAssessmentDoesNotOverclaim
    (criteria : StudyCriteria) :
    controlledStudyReady criteria = false ->
    studyEvidenceLevel criteria = EvidenceLevel.controlledStudyProtocolRun := by
  intro hReady
  simp [studyEvidenceLevel, hReady]

theorem publicEffectivenessEvidenceRequiresProtocol
    (criteria : StudyCriteria)
    (effectiveness : EffectivenessCriteria) :
    publicEvidenceLevel criteria effectiveness =
      PublicEvidenceLevel.controlledStudyEffectiveness ->
    controlledStudyReady criteria = true := by
  intro h
  by_cases hReady : controlledStudyReady criteria = true
  · exact hReady
  · simp [publicEvidenceLevel, hReady] at h

theorem publicEffectivenessEvidenceRequiresEffectivenessReady
    (criteria : StudyCriteria)
    (effectiveness : EffectivenessCriteria) :
    publicEvidenceLevel criteria effectiveness =
      PublicEvidenceLevel.controlledStudyEffectiveness ->
    effectivenessReady effectiveness = true := by
  intro h
  by_cases hReady : controlledStudyReady criteria = true
  · simp [publicEvidenceLevel, hReady] at h
    by_cases hEffectiveness : effectivenessReady effectiveness = true
    · exact hEffectiveness
    · simp [hEffectiveness] at h
  · simp [publicEvidenceLevel, hReady] at h

theorem labelMappingBlocksEffectivenessReady
    (criteria : EffectivenessCriteria) :
    criteria.labelsNotUsedAsSignals = false ->
    effectivenessReady criteria = false := by
  intro h
  simp [effectivenessReady, h]

theorem controlledStudyReadyRequiresAudit
    (criteria : StudyCriteria) :
    controlledStudyReady criteria = true ->
    studyAuditReady criteria = true := by
  intro hReady
  simp [controlledStudyReady] at hReady
  exact hReady.2

theorem controlledStudyReadyRequiresDesign
    (criteria : StudyCriteria) :
    controlledStudyReady criteria = true ->
    studyDesignReady criteria = true := by
  intro hReady
  simp [controlledStudyReady] at hReady
  exact hReady.1

theorem missingMinimumCasesBlocksControlledStudy
    (criteria : StudyCriteria) :
    criteria.scenarioCount < 500 ->
    controlledStudyReady criteria = false := by
  intro hCount
  have hMinimum : decide (500 <= criteria.scenarioCount) = false := by
    simp [Nat.not_le_of_gt hCount]
  simp [controlledStudyReady, studyDesignReady, hMinimum]

theorem jsonWellFormedHasNonnegativeUncertainty
    (input : JsonGateInput) :
    jsonInputWellFormed input ->
    0 <= input.uncertainty := by
  intro h
  exact h.2.1

theorem jsonWellFormedWarnMarginBelowLimit
    (input : JsonGateInput) :
    jsonInputWellFormed input ->
    input.warnMargin < input.limit := by
  intro h
  exact h.2.2.2.2

theorem jsonIncompleteInputBlocks
    (input : JsonGateInput) :
    input.metadataComplete = false ->
    jsonGateVerdict input = Verdict.block := by
  intro h
  simp [jsonGateVerdict, h]

theorem jsonInvalidInputBlocks
    (input : JsonGateInput) :
    isValidInput input = false ->
    jsonGateVerdict input = Verdict.block := by
  intro h
  simp [jsonGateVerdict, h]

theorem jsonCompleteInputUsesIntervalVerdict
    (input : JsonGateInput) :
    input.metadataComplete = true ->
    isValidInput input = true ->
    jsonGateVerdict input =
      intervalVerdict input.upperBound input.limit input.warnMargin := by
  intro hMeta hValid
  simp [jsonGateVerdict, hMeta, hValid]

theorem jsonCompleteBlockCorrect
    (input : JsonGateInput) :
    input.metadataComplete = true ->
    isValidInput input = true ->
    input.upperBound > input.limit ->
    jsonGateVerdict input = Verdict.block := by
  intro hMeta hValid hBlock
  simp [jsonGateVerdict, hMeta, hValid, intervalVerdict, hBlock]

theorem jsonCompleteWarnCorrect
    (input : JsonGateInput) :
    input.metadataComplete = true ->
    isValidInput input = true ->
    input.upperBound > input.limit - input.warnMargin ->
    input.upperBound <= input.limit ->
    jsonGateVerdict input = Verdict.warn := by
  intro hMeta hValid hWarn hLimit
  have hNoBlock : Not (input.upperBound > input.limit) := by
    omega
  simp [jsonGateVerdict, hMeta, hValid, intervalVerdict, hNoBlock, hWarn]

theorem jsonCompletePassCorrect
    (input : JsonGateInput) :
    input.metadataComplete = true ->
    isValidInput input = true ->
    0 <= input.warnMargin ->
    input.upperBound <= input.limit - input.warnMargin ->
    jsonGateVerdict input = Verdict.pass := by
  intro hMeta hValid hMargin hPass
  have hNotBlock : Not (input.upperBound > input.limit) := by
    omega
  have hNotWarn : Not (input.upperBound > input.limit - input.warnMargin) := by
    omega
  simp [jsonGateVerdict, hMeta, hValid, intervalVerdict, hNotBlock, hNotWarn]

theorem jsonGateVerdictDeterministic
    (input : JsonGateInput) :
    Or
      (jsonGateVerdict input = Verdict.pass)
      (Or
        (jsonGateVerdict input = Verdict.warn)
        (jsonGateVerdict input = Verdict.block)) := by
  cases hMeta : input.metadataComplete
  · simp [jsonGateVerdict, hMeta]
  · cases hValid : isValidInput input
    · simp [jsonGateVerdict, hMeta, hValid]
    · simpa [jsonGateVerdict, hMeta, hValid] using
        deterministicVerdict input.upperBound input.limit input.warnMargin

theorem verdictMonotoneWithUpperBound
    (lowerUpper upperBound limit warnMargin : Int) :
    lowerUpper <= upperBound ->
    verdictRank (intervalVerdict lowerUpper limit warnMargin) <=
      verdictRank (intervalVerdict upperBound limit warnMargin) := by
  intro hOrder
  by_cases hUpperBlock : upperBound > limit
  · by_cases hLowerBlock : lowerUpper > limit
    · simp [intervalVerdict, hUpperBlock, hLowerBlock, verdictRank]
    · by_cases hLowerWarn : lowerUpper > limit - warnMargin
      · simp [intervalVerdict, hUpperBlock, hLowerBlock, hLowerWarn, verdictRank]
      · simp [intervalVerdict, hUpperBlock, hLowerBlock, hLowerWarn, verdictRank]
  · have hLowerNotBlock : Not (lowerUpper > limit) := by
      omega
    by_cases hUpperWarn : upperBound > limit - warnMargin
    · by_cases hLowerWarn : lowerUpper > limit - warnMargin
      · simp [
          intervalVerdict,
          hUpperBlock,
          hUpperWarn,
          hLowerNotBlock,
          hLowerWarn,
          verdictRank,
        ]
      · simp [
          intervalVerdict,
          hUpperBlock,
          hUpperWarn,
          hLowerNotBlock,
          hLowerWarn,
          verdictRank,
        ]
    · have hLowerNotWarn : Not (lowerUpper > limit - warnMargin) := by
        omega
      simp [
        intervalVerdict,
        hUpperBlock,
        hUpperWarn,
        hLowerNotBlock,
        hLowerNotWarn,
        verdictRank,
      ]
