import ubinascii
import ujson
import gc
import socket

try:
    import ssl
except ImportError:
    import ussl as ssl


def b64decode_str(s):
    while len(s) % 4 != 0:
        s += "="
    return ubinascii.a2b_base64(s).decode("utf-8")


def extraer_token_desde_buffer(buf):
    i = buf.find("$jwt")
    if i < 0:
        return None

    sub = buf[i:i+300]

    eq = sub.find("=")
    if eq < 0:
        return None

    rhs = sub[eq+1:].lstrip()
    if not rhs:
        return None

    quote = rhs[0]
    if quote not in ("'", '"'):
        return None

    end = rhs.find(quote, 1)
    if end < 0:
        return None

    jwt_b64 = rhs[1:end]
    return b64decode_str(jwt_b64)


def limpiar_chunked_y_parsear(txt):
    txt = txt.lstrip()

    i = txt.find("{")
    if i < 0:
        raise ValueError("No se encontró inicio de JSON")

    txt = txt[i:]

    j = txt.rfind("}")
    if j < 0:
        raise ValueError("No se encontró cierre de JSON")

    txt = txt[:j+1]
    return ujson.loads(txt)


def http_get_text_small(host, path, chunk_size=1024, max_keep=2000):
    addr = socket.getaddrinfo(host, 443)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s = ssl.wrap_socket(s, server_hostname=host)

    req = (
        "GET {} HTTP/1.1\r\n"
        "Host: {}\r\n"
        "User-Agent: MicroPythonESP32\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).format(path, host)

    s.write(req.encode())

    data = b""
    while b"\r\n\r\n" not in data:
        chunk = s.read(chunk_size)
        if not chunk:
            break
        data += chunk
        if len(data) > 8192:
            break

    pos = data.find(b"\r\n\r\n")
    if pos >= 0:
        body = data[pos+4:]
    else:
        body = b""

    text_accum = body.decode("utf-8", "ignore")

    while True:
        gc.collect()
        chunk = s.read(chunk_size)
        if not chunk:
            break
        text_accum += chunk.decode("utf-8", "ignore")

        if len(text_accum) > max_keep:
            text_accum = text_accum[-max_keep:]

    s.close()
    return text_accum


def extraer_token_paradero(codsimt):
    host = "www.red.cl"
    path = "/planifica-tu-viaje/cuando-llega/?codsimt=" + codsimt

    addr = socket.getaddrinfo(host, 443)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s = ssl.wrap_socket(s, server_hostname=host)

    req = (
        "GET {} HTTP/1.1\r\n"
        "Host: {}\r\n"
        "User-Agent: MicroPythonESP32\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).format(path, host)

    s.write(req.encode())

    data = b""
    while b"\r\n\r\n" not in data:
        chunk = s.read(512)
        if not chunk:
            break
        data += chunk
        if len(data) > 8192:
            break

    pos = data.find(b"\r\n\r\n")
    if pos >= 0:
        body = data[pos+4:]
    else:
        body = b""

    buf = body.decode("utf-8", "ignore")
    token = extraer_token_desde_buffer(buf)
    if token:
        s.close()
        return token

    while True:
        gc.collect()
        chunk = s.read(1024)
        if not chunk:
            break

        buf += chunk.decode("utf-8", "ignore")

        if len(buf) > 3000:
            buf = buf[-3000:]

        token = extraer_token_desde_buffer(buf)
        if token:
            s.close()
            return token

    s.close()
    raise RuntimeError("No se pudo extraer el token $jwt")


def consultar_prediccion(codsimt, token):
    host = "www.red.cl"
    paths = [
        "/predictorPlus/prediccion?t={}&codsimt={}&codser=".format(token, codsimt),
        "/predictor/prediccion?t={}&codsimt={}&codser=".format(token, codsimt),
    ]

    for path in paths:
        gc.collect()
        try:
            txt = http_get_text_small(host, path, chunk_size=1024, max_keep=12000)

            try:
                data = ujson.loads(txt)
            except Exception:
                data = limpiar_chunked_y_parsear(txt)

            return {
                "ok": True,
                "path": path,
                "data": data
            }

        except Exception as e:
            print("Falló:", e)

    return {
        "ok": False,
        "error": "No se pudo consultar predictor",
        "data": {}
    }


def get_paradero(codsimt):
    token = extraer_token_paradero(codsimt)
    return consultar_prediccion(codsimt, token)

