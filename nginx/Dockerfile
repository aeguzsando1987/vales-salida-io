FROM nginx:alpine

# openssl para generar el certificado SSL en el entrypoint
RUN apk add --no-cache openssl

# Configuración de nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Entrypoint: genera cert al iniciar si no existe
COPY entrypoint.sh /entrypoint.sh
# Eliminar saltos de línea Windows (CRLF→LF) para que Linux pueda ejecutarlo
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 80 443

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
