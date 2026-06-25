"""
Enterprise Edition (EE) module.

Contains features available only in the Enterprise Edition:
- auth/       Keycloak SSO provider, enterprise role resolver
- cmdb/       CMDB synchronization client and scheduler
- email/      BCT enterprise email provider
- telemetry/  Agent Watch telemetry adapter

These modules are loaded conditionally when EE_ENABLED=true.
In OSS mode, the system runs with basic authentication and stub providers.
"""
