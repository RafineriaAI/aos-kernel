import Std

namespace AOSEnvironmentModel

inductive EnvVerdict where
  | pass
  | warn
  | block
  deriving DecidableEq, Repr

structure EnvSignal where
  score : Int
  uncertainty : Int
  metadataComplete : Bool
  deriving DecidableEq, Repr

structure EnvPolicy where
  limit : Int
  warnMargin : Int
  deriving DecidableEq, Repr

structure ReplayRecord where
  expected : EnvVerdict
  observed : EnvVerdict
  inputPresent : Bool
  digestPresent : Bool
  deriving DecidableEq, Repr

structure TransactionDigestVector where
  eventDigest1 : String
  eventDigest2 : String
  eventDigest3 : String
  chainDigest : String
  formalHashImplementationClaim : Bool
  pythonLeanRefinementClaim : Bool
  deriving DecidableEq, Repr

structure EnvironmentBoundary where
  pythonLeanRefinementClaim : Bool
  implementationCorrectnessClaim : Bool
  deploymentAssuranceClaim : Bool
  deriving DecidableEq, Repr

def EnvSignal.upperBound (signal : EnvSignal) : Int :=
  signal.score + signal.uncertainty

def envInputWellFormed (signal : EnvSignal) (policy : EnvPolicy) : Prop :=
  0 <= signal.score ∧
    0 <= signal.uncertainty ∧
    0 <= policy.limit ∧
    0 <= policy.warnMargin ∧
    policy.warnMargin < policy.limit

def isValidEnvInput (signal : EnvSignal) (policy : EnvPolicy) : Bool :=
  decide (0 <= signal.score) &&
  decide (0 <= signal.uncertainty) &&
  decide (0 <= policy.limit) &&
  decide (0 <= policy.warnMargin) &&
  decide (policy.warnMargin < policy.limit)

def envVerdict (signal : EnvSignal) (policy : EnvPolicy) : EnvVerdict :=
  if signal.metadataComplete && isValidEnvInput signal policy then
    if signal.upperBound > policy.limit then EnvVerdict.block
    else if signal.upperBound > policy.limit - policy.warnMargin then
      EnvVerdict.warn
    else
      EnvVerdict.pass
  else
    EnvVerdict.block

def replayReady (record : ReplayRecord) : Bool :=
  record.inputPresent && record.digestPresent

def replayMatches (record : ReplayRecord) : Prop :=
  record.expected = record.observed

def publicBoundary : EnvironmentBoundary := {
  pythonLeanRefinementClaim := false
  implementationCorrectnessClaim := false
  deploymentAssuranceClaim := false
}

def canonicalTransactionDigestVector : TransactionDigestVector := {
  eventDigest1 :=
    "sha256:f712ac474cdf417f13c146a7da4f8daf4912e0f2e7949ede5e37e951a6f93c45"
  eventDigest2 :=
    "sha256:df918c73a172b543bccd9b383cf2d79d753a170c7f6c5770a2a7f0121211a255"
  eventDigest3 :=
    "sha256:24eee4a1a50b3fa960f5665d105c9f854e7acd0801bd8467d811d02e038b3eda"
  chainDigest :=
    "sha256:6f270a03ca0461fab4ce5b382b1f927ef3e28c68bb5e98e9e63cc35cecf98d42"
  formalHashImplementationClaim := false
  pythonLeanRefinementClaim := false
}

theorem isValidEnvInputTrueIffWellFormed
    (signal : EnvSignal)
    (policy : EnvPolicy) :
    isValidEnvInput signal policy = true ↔ envInputWellFormed signal policy := by
  simp [isValidEnvInput, envInputWellFormed, and_assoc]

theorem incompleteMetadataBlocks
    (signal : EnvSignal)
    (policy : EnvPolicy) :
    signal.metadataComplete = false ->
    envVerdict signal policy = EnvVerdict.block := by
  intro h
  simp [envVerdict, h]

theorem invalidInputBlocks
    (signal : EnvSignal)
    (policy : EnvPolicy) :
    isValidEnvInput signal policy = false ->
    envVerdict signal policy = EnvVerdict.block := by
  intro h
  simp [envVerdict, h]

theorem completeBlockCondition
    (signal : EnvSignal)
    (policy : EnvPolicy) :
    signal.metadataComplete = true ->
    isValidEnvInput signal policy = true ->
    signal.upperBound > policy.limit ->
    envVerdict signal policy = EnvVerdict.block := by
  intro hComplete hValid hBlock
  simp [envVerdict, hComplete, hValid, hBlock]

theorem completePassRelation
    (signal : EnvSignal)
    (policy : EnvPolicy) :
    signal.metadataComplete = true ->
    isValidEnvInput signal policy = true ->
    0 <= policy.warnMargin ->
    signal.upperBound <= policy.limit - policy.warnMargin ->
    envVerdict signal policy = EnvVerdict.pass := by
  intro hComplete hValid hMargin hPass
  have hNotBlock : Not (signal.upperBound > policy.limit) := by
    omega
  have hNotWarn : Not (signal.upperBound > policy.limit - policy.warnMargin) := by
    omega
  simp [envVerdict, hComplete, hValid, hNotBlock, hNotWarn]

theorem completeWarnRelation
    (signal : EnvSignal)
    (policy : EnvPolicy) :
    signal.metadataComplete = true ->
    isValidEnvInput signal policy = true ->
    signal.upperBound > policy.limit - policy.warnMargin ->
    signal.upperBound <= policy.limit ->
    envVerdict signal policy = EnvVerdict.warn := by
  intro hComplete hValid hWarn hLimit
  have hNotBlock : Not (signal.upperBound > policy.limit) := by
    omega
  simp [envVerdict, hComplete, hValid, hNotBlock, hWarn]

theorem completeBlockRelation
    (signal : EnvSignal)
    (policy : EnvPolicy) :
    signal.metadataComplete = true ->
    isValidEnvInput signal policy = true ->
    signal.upperBound > policy.limit ->
    envVerdict signal policy = EnvVerdict.block := by
  exact completeBlockCondition signal policy

theorem completePassCondition
    (signal : EnvSignal)
    (policy : EnvPolicy) :
    signal.metadataComplete = true ->
    isValidEnvInput signal policy = true ->
    Not (signal.upperBound > policy.limit) ->
    Not (signal.upperBound > policy.limit - policy.warnMargin) ->
    envVerdict signal policy = EnvVerdict.pass := by
  intro hComplete hValid hNotBlock hNotWarn
  simp [envVerdict, hComplete, hValid, hNotBlock, hNotWarn]

theorem verdictDeterministic
    (signal : EnvSignal)
    (policy : EnvPolicy) :
    Or
      (envVerdict signal policy = EnvVerdict.pass)
      (Or
        (envVerdict signal policy = EnvVerdict.warn)
        (envVerdict signal policy = EnvVerdict.block)) := by
  cases envVerdict signal policy <;> simp

theorem replayReadyHasInput
    (record : ReplayRecord) :
    replayReady record = true ->
    record.inputPresent = true := by
  intro h
  simp [replayReady] at h
  exact h.1

theorem replayReadyHasDigest
    (record : ReplayRecord) :
    replayReady record = true ->
    record.digestPresent = true := by
  intro h
  simp [replayReady] at h
  exact h.2

theorem replayMatchIsExact
    (record : ReplayRecord) :
    replayMatches record ->
    record.expected = record.observed := by
  intro h
  exact h

theorem publicBoundaryDoesNotClaimRefinement :
    publicBoundary.pythonLeanRefinementClaim = false := by
  rfl

theorem publicBoundaryDoesNotClaimImplementationCorrectness :
    publicBoundary.implementationCorrectnessClaim = false := by
  rfl

theorem publicBoundaryDoesNotClaimDeploymentAssurance :
    publicBoundary.deploymentAssuranceClaim = false := by
  rfl

theorem canonicalTransactionDigestEvent1MatchesVector :
    canonicalTransactionDigestVector.eventDigest1 =
      "sha256:f712ac474cdf417f13c146a7da4f8daf4912e0f2e7949ede5e37e951a6f93c45" := by
  rfl

theorem canonicalTransactionDigestChainMatchesVector :
    canonicalTransactionDigestVector.chainDigest =
      "sha256:6f270a03ca0461fab4ce5b382b1f927ef3e28c68bb5e98e9e63cc35cecf98d42" := by
  rfl

theorem canonicalTransactionDigestDoesNotClaimFormalHashImplementation :
    canonicalTransactionDigestVector.formalHashImplementationClaim = false := by
  rfl

theorem canonicalTransactionDigestDoesNotClaimPythonLeanRefinement :
    canonicalTransactionDigestVector.pythonLeanRefinementClaim = false := by
  rfl

end AOSEnvironmentModel
