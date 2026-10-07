# How This Site Is Secured

## 1. Who issued your certificate, which domain names it covers, and when it expires.

Let's Encrypt, kenwinsor.xyz, expires Jan 4 2027

## 2. How renewal works and what your renewal test and timer check showed.

The certificate expires in 90 days and renewal is automatic through certbots timer. Renewal test shows Renewal Succeeded and timer check showed when it ran last, when it will run again, and the timers name.

## 3. Which ports are open to the internet, why each is open, and who can connect to your SSH port.

80 is open as HTTP and is used by nginx, 443 is HTTPS and is used by nginx and is how users connect. 22 is SSH and only my two IPs i allowed can connect with the key.

## 4. Where encryption starts and ends, including the connection from Nginx to the app on your VM.

encryption starts on the visitors end on the browser and ends at nginx at the VM. nginx to the app is HTTP.

## 5. The actual openssl output from section 6 of the guide, showing your certificate's subject, issuer, and validity dates.

```
$ echo | openssl s_client -connect kenwinsor.xyz:443 -servername kenwinsor.xyz 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
subject=CN=kenwinsor.xyz
issuer=C=US, O=Let's Encrypt, CN=YE1
notBefore=Oct  6 21:12:54 2026 GMT
notAfter=Jan  4 21:12:53 2027 GMT
X509v3 Subject Alternative Name:
    DNS:kenwinsor.xyz, DNS:www.kenwinsor.xyz
```
