import secrets
import string

def generar_clave_segura(longitud=50):
    # Usamos letras (mayúsculas/minúsculas) y números
    # Eliminamos caracteres como \, $, ", ' y # para evitar problemas en .env
    caracteres_seguros = string.ascii_letters + string.digits + "!@*()-_=+"
    
    # Generamos la clave usando secretos criptográficamente seguros
    nueva_clave = ''.join(secrets.choice(caracteres_seguros) for _ in range(longitud))
    
    print("\n--- NUEVA SECRET_KEY SEGURA ---")
    print(nueva_clave)
    print("--------------------------------\n")
    print("Copia esta clave en tu archivo .env sin comillas.")

if __name__ == "__main__":
    generar_clave_segura()