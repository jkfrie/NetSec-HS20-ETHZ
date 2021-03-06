import util
import json
import hashlib
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend as default_backend

def create_rsa_private_key():
    private_key = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048
    )
    return private_key

def get_jwk_from_public_key(public_key):
    e = public_key.public_numbers().e
    n = public_key.public_numbers().n
    e = util.to_base64(util.int_to_bytes(e))
    n = util.to_base64(util.int_to_bytes(n))
    my_jwk = {
        "kty": "RSA",
        "n": n,
        "e": e
    }
    return my_jwk

def get_jws(protected_header, payload, private_key):
    protected_header = util.to_base64(json.dumps(protected_header))
    if (payload != ""): 
        payload = util.to_base64(json.dumps(payload))
    message = protected_header + "." + payload
    signature = private_key.sign(
        message.encode('utf8'),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    signature = util.to_base64(signature)
    jws = {}
    jws["protected"] = protected_header
    jws["payload"] = payload
    jws["signature"] = signature
    jws = json.dumps(jws).encode("utf8")
    return jws

def write_private_key(private_key, filename):
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(filename, 'wb') as f:
        f.write(pem)
        f.close()

def write_public_key(public_key, filename):
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(filename, 'wb') as f:
        f.write(pem)
        f.close()

def write_certificate(cert, filename):
    cert = x509.load_pem_x509_certificate(cert, default_backend())
    pem = cert.public_bytes(serialization.Encoding.PEM)
    with open(filename, 'wb') as f:
        f.write(pem)
        f.close()

def load_private_key(filename):
    with open(filename, "rb") as f:
        private = serialization.load_pem_private_key(
            f.read(), None, backend=default_backend()
        )
        f.close()
    return private

def pem_to_der_certificate(cert):
    cert = x509.load_pem_x509_certificate(cert, default_backend())
    return cert.public_bytes(Encoding.DER)

def get_key_authorization(token, jwk):
    jwk = json.dumps(jwk, sort_keys=True, separators=(',', ':')).encode('utf8')
    thumbprint = hashlib.sha256(jwk).digest()
    thumbprint = util.to_base64(thumbprint)
    return token + "." + thumbprint

def get_csr(domains, private_key):
    domain_names = []
    for domain in domains:
        domain_names.append(x509.DNSName(domain))

    builder = x509.CertificateSigningRequestBuilder()
    builder = builder.subject_name(x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, domains[0])]))
    builder = builder.add_extension(x509.SubjectAlternativeName(
        domain_names), critical=False)
    request = builder.sign(private_key, hashes.SHA256(), default_backend())
    request = util.to_base64(request.public_bytes(Encoding.DER))
    return request
