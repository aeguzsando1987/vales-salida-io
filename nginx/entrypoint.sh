#!/bin/sh

CERT_DIR="/etc/nginx/certs"
CERT_FILE="${CERT_DIR}/server.crt"
KEY_FILE="${CERT_DIR}/server.key"
VPN_IP="${SERVER_IP:-26.32.18.150}"
LOCAL_IP="${LOCAL_IP:-192.168.1.10}"

# Generar certificado si no existe (persiste en volumen Docker)
if [ ! -f "$CERT_FILE" ]; then
    echo "[nginx] Generando certificado SSL para IPs: ${VPN_IP}, ${LOCAL_IP}"
    mkdir -p "$CERT_DIR"

    openssl req -x509 -nodes -days 730 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "/C=MX/O=Sistema de Vales/CN=${VPN_IP}" \
        -addext "subjectAltName=IP:${VPN_IP},IP:${LOCAL_IP},IP:127.0.0.1,DNS:localhost" \
        2>/dev/null

    echo "[nginx] Certificado generado. Válido por 2 años."
else
    echo "[nginx] Certificado existente encontrado, reutilizando."
fi

exec "$@"
