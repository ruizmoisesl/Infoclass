#!/usr/bin/env python3
"""
Script de prueba para verificar la detección de tipos MIME
"""

import mimetypes
import os

def get_mime_type_by_extension(extension):
    """Obtener tipo MIME por extensión de archivo"""
    mime_types = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'txt': 'text/plain',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'svg': 'image/svg+xml',
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
        '7z': 'application/x-7z-compressed',
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'csv': 'text/csv',
        'json': 'application/json',
        'xml': 'application/xml',
        'html': 'text/html',
        'css': 'text/css',
        'js': 'application/javascript',
        'py': 'text/x-python',
        'java': 'text/x-java-source',
        'cpp': 'text/x-c++src',
        'c': 'text/x-csrc',
        'h': 'text/x-chdr',
        'php': 'application/x-httpd-php',
        'sql': 'application/sql',
        'md': 'text/markdown',
        'rtf': 'application/rtf'
    }
    return mime_types.get(extension.lower(), 'application/octet-stream')

def test_mime_detection():
    """Probar la detección de tipos MIME"""
    
    test_files = [
        'documento.pdf',
        'imagen.jpg',
        'presentacion.pptx',
        'hoja_calculo.xlsx',
        'texto.txt',
        'video.mp4',
        'audio.mp3',
        'archivo.zip',
        'codigo.py',
        'pagina.html'
    ]
    
    print("🧪 Probando detección de tipos MIME...")
    print("=" * 50)
    
    for filename in test_files:
        # Método 1: mimetypes.guess_type()
        mime_type_1, _ = mimetypes.guess_type(filename)
        
        # Método 2: Por extensión
        extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        mime_type_2 = get_mime_type_by_extension(extension)
        
        print(f"📁 {filename}")
        print(f"   mimetypes.guess_type(): {mime_type_1 or 'No detectado'}")
        print(f"   Por extensión:         {mime_type_2}")
        print()
    
    print("✅ Prueba completada")

if __name__ == '__main__':
    test_mime_detection()
