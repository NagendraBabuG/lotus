import ssl
import socket

def create_secure_context():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)  # or Purpose.SERVER_AUTH for client

    # Restrict to modern TLS 1.3 only (best security)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    # Prioritize X25519 (and other strong groups)
    # Note: set_ecdh_curve() is legacy; use set_groups() or SSL_CTX_set1_groups_list in newer OpenSSL
    try:
        # Preferred way in recent Python/OpenSSL
        context.set_groups("X25519:X25519MLKEM768:P-256")  # Hybrid if supported
    except AttributeError:
        # Fallback for older Python
        context.set_ciphers("TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256")
        # X25519 is usually default in TLS 1.3

    # Strong ciphers
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:!aNULL:!eNULL:!LOW:!3DES')

    return context

# Server example
def run_server():
    context = create_secure_context()
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('0.0.0.0', 8443))
        sock.listen(5)
        with context.wrap_socket(sock, server_side=True) as ssock:
            conn, addr = ssock.accept()
            # handle connection...
