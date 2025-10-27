from io import BytesIO
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import os

def generate_restaurant_pdf(restaurant):
    """Генерация PDF документа для ресторана"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Заголовок
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Ресторан: {restaurant.name}")
    
    # Информация о ресторане
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Тип кухни: {restaurant.get_cuisine_type_display()}")
    p.drawString(50, height - 100, f"Адрес: {restaurant.address}")
    p.drawString(50, height - 120, f"Телефон: {restaurant.phone}")
    p.drawString(50, height - 140, f"Часы работы: {restaurant.opening_hours}")
    
    # Изображение ресторана
    if restaurant.image and os.path.exists(restaurant.image.path):
        try:
            image = ImageReader(restaurant.image.path)
            p.drawImage(image, 400, height - 150, width=100, height=75)
        except:
            p.drawString(400, height - 150, "Изображение недоступно")
    
    # Список столиков
    p.drawString(50, height - 180, "Столики:")
    y_position = height - 200
    
    for table in restaurant.tables.all():
        if y_position < 100:
            p.showPage()
            y_position = height - 50
        p.drawString(70, y_position, f"• Столик {table.table_number}: {table.capacity} чел., {table.price_per_hour} руб./час")
        y_position -= 20
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer