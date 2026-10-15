# KALI Controlled Internet Gateway (STEP 24)

## Overview
The KALI Internet Gateway acts as the sole outbound proxy/mediator for all web interactions requested by the model. It sits strictly after the **Permission Manager** in the executor flow:

`KALI Model → Permission Manager (Approval/Risk) → Internet Gateway → Network Policy / SSRF Check → External Web`

## Security Protections

### Server-Side Request Forgery (SSRF) Protection
To prevent the model from hitting internal infrastructure (e.g., metadata endpoints, local databases, routers), the gateway implements DNS resolution and CIDR-based checks on every URL *before* initiating a request.
- **Blocked ranges**: Loopback (`127.x.x.x`), Private Networks (`10.x.x.x`, `192.168.x.x`, `172.16.x.x`), Link Local, Multicast.
- **DNS Rebinding Protection**: The URL hostname is resolved to an IP Address locally by the gateway (`socket.gethostbyname`). The IP is verified against private lists using Python's `ipaddress` library before the request is allowed.

### Protocol Restrictions
- **HTTPS Only (Default)**: Unencrypted HTTP is denied by default to prevent MITM. This can be enabled selectively via `NetworkPolicy`.

### Resource Controls
- **Size Limits**: Responses are streamed and truncated/blocked if they exceed the `max_response_bytes` (Default 10MB) to prevent OOM/DoS scenarios.
- **Timeouts**: Hard timeouts (Default 10s) prevent the model from hanging indefinitely.
- **Redirects**: Clients do not automatically follow redirects using underlying libraries. Redirects are trapped, counted, and passed back through the SSRF protection mechanism to prevent a safe domain from redirecting the gateway into an internal IP. Max redirects are limited (Default 3).

### Domain Policies
Project or System level allow/deny lists can be passed via `DomainPolicy`.
- A filled allow-list defaults the gateway to DENY all other domains.
- A filled deny-list explicitly blocks specific domains.

## Components
- **`InternetGateway`**: The core manager routing requests.
- **`HTTPClient`**: A safe HTTP requester backed by `httpx` implementing the chunking and manual redirect logic.
- **`URLValidator` & `SSRFProtection`**: The validation gates.
