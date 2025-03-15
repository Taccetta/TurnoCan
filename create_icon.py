from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """
    Crea un icono simple para la aplicación TurnosCan
    """
    # Crear una imagen cuadrada
    img_size = 128
    img = Image.new('RGBA', (img_size, img_size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Color verde similar al usado en la aplicación
    green_color = (69, 160, 73)
    
    # Dibujar un círculo de fondo
    circle_margin = 2
    circle_size = img_size - 2 * circle_margin
    draw.ellipse((circle_margin, circle_margin, circle_margin + circle_size, circle_margin + circle_size), 
                 fill=green_color)
    
    # Intentar cargar una fuente, o usar default si no está disponible
    try:
        # Probar con una fuente del sistema
        font = ImageFont.truetype("arial.ttf", size=80)
    except IOError:
        # Si no se encuentra, usar una fuente por defecto
        font = ImageFont.load_default()
    
    # Dibujar una "T" y una "C" (para TurnosCan) en blanco
    text = "TC"
    text_color = (255, 255, 255)
    
    # Calcular la posición del texto (centrado)
    text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (60, 60)
    text_position = ((img_size - text_width) // 2, (img_size - text_height) // 2 - 10)
    
    # Dibujar el texto
    draw.text(text_position, text, fill=text_color, font=font)
    
    # Guardar la imagen como icono
    img.save("icon.png")
    
    print(f"Icono creado en {os.path.abspath('icon.png')}")

if __name__ == "__main__":
    create_icon() 