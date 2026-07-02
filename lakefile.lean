import Lake
open Lake DSL

package AOSPublicCore where

@[default_target]
lean_lib «AOSPublicCore» where
  srcDir := "lean"
  roots := #[`AOSPublicCore, `AOSEnvironmentModel, `AOSAxiomAudit]
