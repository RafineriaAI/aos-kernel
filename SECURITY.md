# Security Policy

Report security issues confidentially to the maintainer through GitHub private
vulnerability reporting:
[Report a vulnerability](https://github.com/RafineriaAI/aos-kernel/security/advisories/new)
(repository **Security** tab -> **Report a vulnerability**).

Do not open public issues, pull requests, discussions, comments, screenshots, or
logs containing secrets, credentials, controlled datasets, model weights,
deployment details, controlled records, partner information,
vulnerability exploit details, or technical material outside the public
demonstrator.

This repository is a limited demonstrator. It does not contain the production
AOS Core, production security design, delivery materials, or
deployment design.

Security reports do not grant permission to copy, exploit, publish, disclose,
redistribute, commercialize, or derive products from AOS material. Coordinated
handling and written maintainer approval are required before any public
disclosure.

Production systems require separate security engineering, including:

- KMS-backed key handling
- key rotation and revocation
- ACLs and least privilege
- log retention and deletion policy
- incident response workflow
- supply-chain review
- secret scanning
- environment-specific policy review
- dependency and build provenance review
- confidential vulnerability intake and disclosure process

Do not infer production security properties from this public demonstrator.
