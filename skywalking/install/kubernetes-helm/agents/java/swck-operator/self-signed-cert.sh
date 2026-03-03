#!/bin/bash
# =============================================================================
# Generate self-signed certificate for webhook (if cert-manager not available)
# =============================================================================

set -euo pipefail

NAMESPACE="skywalking-swck-system"
SERVICE="skywalking-swck-controller-manager-service"
SECRET="skywalking-swck-controller-manager-cert"

TMPDIR=$(mktemp -d)
trap "rm -rf ${TMPDIR}" EXIT

echo "Generating self-signed certificate for SWCK webhook..."

# Generate CA
openssl genrsa -out ${TMPDIR}/ca.key 2048
openssl req -x509 -new -nodes -key ${TMPDIR}/ca.key -sha256 -days 3650 \
    -out ${TMPDIR}/ca.crt -subj "/CN=skywalking-swck-ca"

# Generate server key and CSR
openssl genrsa -out ${TMPDIR}/server.key 2048

cat > ${TMPDIR}/csr.conf << EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = ${SERVICE}
DNS.2 = ${SERVICE}.${NAMESPACE}
DNS.3 = ${SERVICE}.${NAMESPACE}.svc
DNS.4 = ${SERVICE}.${NAMESPACE}.svc.cluster.local
EOF

openssl req -new -key ${TMPDIR}/server.key -out ${TMPDIR}/server.csr \
    -subj "/CN=${SERVICE}.${NAMESPACE}.svc" -config ${TMPDIR}/csr.conf

# Sign the certificate
openssl x509 -req -in ${TMPDIR}/server.csr -CA ${TMPDIR}/ca.crt -CAkey ${TMPDIR}/ca.key \
    -CAcreateserial -out ${TMPDIR}/server.crt -days 3650 \
    -extensions v3_req -extfile ${TMPDIR}/csr.conf

# Create namespace if not exists
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Create secret
kubectl create secret tls ${SECRET} \
    --cert=${TMPDIR}/server.crt \
    --key=${TMPDIR}/server.key \
    -n ${NAMESPACE} \
    --dry-run=client -o yaml | kubectl apply -f -

# Get CA bundle for webhook
CA_BUNDLE=$(cat ${TMPDIR}/ca.crt | base64 | tr -d '\n')

echo ""
echo "Certificate created successfully!"
echo ""
echo "CA Bundle (base64):"
echo "${CA_BUNDLE}"
echo ""

# Export for use in deploy.sh
export SWCK_CA_BUNDLE="${CA_BUNDLE}"
