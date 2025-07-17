#!/usr/bin/env python3
"""
Servidor de prueba para validación biométrica
Uso: python3 test_server.py
"""

import http.server
import socketserver
import ssl
import os
from urllib.parse import urlparse, parse_qs
import json
from datetime import datetime

PORT = 8443  # Puerto HTTPS

class BiometricHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/biometric_auth.html':
            # Servir la página de autenticación biométrica
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                with open('biometric_auth.html', 'r', encoding='utf-8') as f:
                    content = f.read()
                self.wfile.write(content.encode('utf-8'))
            except FileNotFoundError:
                self.send_error(404, "biometric_auth.html not found")
                
        elif parsed_path.path == '/api/validate-token':
            # Endpoint para validar tokens (opcional)
            query_params = parse_qs(parsed_path.query)
            token = query_params.get('token', [None])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Validar token básico
            is_valid = token and token.startswith('AUTH_')
            response = {
                'valid': is_valid,
                'token': token,
                'timestamp': datetime.now().isoformat(),
                'message': 'Token válido' if is_valid else 'Token inválido'
            }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        else:
            # Servir otros archivos estáticamente
            super().do_GET()
    
    def log_message(self, format, *args):
        # Log personalizado
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def create_self_signed_cert():
    """Crear certificado autofirmado para pruebas HTTPS"""
    try:
        import subprocess
        
        # Verificar si ya existe
        if os.path.exists('server.pem'):
            return True
            
        # Crear certificado autofirmado
        cmd = [
            'openssl', 'req', '-new', '-x509', '-keyout', 'server.pem', 
            '-out', 'server.pem', '-days', '365', '-nodes',
            '-subj', '/C=CL/ST=Santiago/L=Santiago/O=ArcoPrime/CN=localhost'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Certificado SSL autofirmado creado")
            return True
        else:
            print(f"❌ Error creando certificado: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔐 Servidor de Validación Biométrica")
    print("=" * 40)
    
    # Verificar archivos necesarios
    if not os.path.exists('biometric_auth.html'):
        print("❌ Error: biometric_auth.html no encontrado")
        print("   Asegúrate de que esté en el mismo directorio")
        return
    
    # Crear certificado para HTTPS (requerido por WebAuthn)
    if not create_self_signed_cert():
        print("⚠️  Advertencia: No se pudo crear certificado SSL")
        print("   WebAuthn requiere HTTPS para funcionar")
    
    # Configurar servidor
    with socketserver.TCPServer(("", PORT), BiometricHandler) as httpd:
        print(f"🚀 Servidor iniciado en puerto {PORT}")
        
        # Configurar SSL si hay certificado
        if os.path.exists('server.pem'):
            httpd.socket = ssl.wrap_socket(
                httpd.socket,
                certfile='server.pem',
                server_side=True
            )
            print(f"🔒 HTTPS habilitado: https://localhost:{PORT}/biometric_auth.html")
        else:
            print(f"🌐 HTTP disponible: http://localhost:{PORT}/biometric_auth.html")
            print("⚠️  Nota: WebAuthn requiere HTTPS en producción")
        
        print("\n📱 URLs de prueba:")
        protocol = "https" if os.path.exists('server.pem') else "http"
        print(f"   {protocol}://localhost:{PORT}/biometric_auth.html?chatId=123456&userId=TestUser")
        print(f"   {protocol}://localhost:{PORT}/api/validate-token?token=AUTH_123_1234567890_abc")
        
        print("\n🛑 Presiona Ctrl+C para detener el servidor")
        print("=" * 40)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Servidor detenido")
            print("✅ Limpieza completada")

if __name__ == "__main__":
    main()