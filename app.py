from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import os
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Flowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.barcode import qr
from reportlab.graphics import renderPDF
from PIL import Image as PILImage, ImageDraw, ImageFont
# Import the weather service module
from weather_service import get_location_key, get_weather_for_date, get_weather_icon_class, get_lawn_care_recommendation
# Add logger configuration at the top of the file
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yard_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set default city for weather forecasts
DEFAULT_CITY = "Johannesburg"

db = SQLAlchemy(app)


# Models
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    yard_size = db.Column(db.Integer, nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    additional_services = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Add city field for weather forecasts
    city = db.Column(db.String(100), default=DEFAULT_CITY)


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    icon = db.Column(db.String(50), nullable=False)


class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)


# Function to create a placeholder logo
def create_placeholder_logo(path):
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Create a new image with a turquoise background
    width, height = 150, 150
    image = PILImage.new('RGB', (width, height), (30, 172, 172))  # Turquoise color #1eacac
    draw = ImageDraw.Draw(image)

    # Draw text
    try:
        # Try to use a font if available
        font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        # If font not available, use default
        font = ImageFont.load_default()

    text = "Yard Portal"
    text_width = draw.textlength(text, font=font)
    text_position = ((width - text_width) // 2, height // 2 - 12)
    draw.text(text_position, text, fill=(255, 255, 255), font=font)

    # Save the image
    image.save(path)
    return path


# Function to create a Yard Portal logo
def create_yard_portal_logo(path):
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Create a new image with a white background
    width, height = 300, 300
    image = PILImage.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    # Draw a circle with the turquoise color
    circle_x, circle_y = width // 2, height // 2
    circle_radius = 120
    draw.ellipse(
        (circle_x - circle_radius, circle_y - circle_radius,
         circle_x + circle_radius, circle_y + circle_radius),
        fill=(30, 172, 172, 255)  # Turquoise color #1eacac
    )

    # Draw a yard/garden icon in white
    # This is a simplified representation of a yard
    # Draw a house
    house_width, house_height = 80, 60
    house_left = circle_x - house_width // 2
    house_top = circle_y - house_height // 2 - 20

    # House base
    draw.rectangle(
        (house_left, house_top + 20, house_left + house_width, house_top + house_height),
        fill=(255, 255, 255, 255)
    )

    # House roof
    draw.polygon(
        [(house_left, house_top + 20),
         (house_left + house_width // 2, house_top),
         (house_left + house_width, house_top + 20)],
        fill=(255, 255, 255, 255)
    )

    # Draw some grass/plants
    for i in range(5):
        x_pos = house_left + 10 + i * 15
        y_base = house_top + house_height + 10

        # Draw a simple plant
        draw.rectangle(
            (x_pos, y_base, x_pos + 5, y_base + 15),
            fill=(255, 255, 255, 255)
        )

        # Draw leaves
        draw.ellipse(
            (x_pos - 5, y_base - 10, x_pos + 10, y_base + 5),
            fill=(255, 255, 255, 255)
        )

    # Save the image
    image.save(path)
    return path


# Routes
@app.route('/')
def home():
    services = Service.query.all()
    testimonials = Testimonial.query.all()
    return render_template('index.html', services=services, testimonials=testimonials)


@app.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        # Process booking form
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        date_str = request.form.get('date')
        time_slot = request.form.get('time_slot')
        yard_size = int(request.form.get('yard_size'))
        service_type = request.form.get('service_type')
        additional_services = ','.join(request.form.getlist('additional_services'))
        price = float(request.form.get('price'))
        city = request.form.get('city', DEFAULT_CITY)

        # Convert date string to date object
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Create new booking
        new_booking = Booking(
            name=name,
            email=email,
            phone=phone,
            address=address,
            date=date_obj,
            time_slot=time_slot,
            yard_size=yard_size,
            service_type=service_type,
            additional_services=additional_services,
            price=price,
            city=city
        )

        db.session.add(new_booking)
        db.session.commit()

        flash('Your booking has been confirmed! Thank you for choosing Yard Portal.', 'success')
        return redirect(url_for('booking_confirmation', booking_id=new_booking.id))

    # GET request - show booking form
    services = Service.query.all()

    # Generate available dates (next 14 days)
    today = datetime.now().date()
    available_dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 15)]

    # Time slots
    time_slots = [
        "8:00 AM - 10:00 AM",
        "10:00 AM - 12:00 PM",
        "12:00 PM - 2:00 PM",
        "2:00 PM - 4:00 PM",
        "4:00 PM - 6:00 PM"
    ]

    return render_template('book.html',
                           available_dates=available_dates,
                           time_slots=time_slots,
                           services=services)


@app.route('/quote')
def quote():
    services = Service.query.all()
    additional_services = [
        {"id": "edging", "name": "Edging", "price": 15},
        {"id": "trimming", "name": "Shrub Trimming", "price": 25},
        {"id": "cleanup", "name": "Debris Cleanup", "price": 20}
    ]
    return render_template('quote.html', services=services, additional_services=additional_services)


@app.route('/calculate_quote', methods=['POST'])
def calculate_quote():
    data = request.get_json()

    yard_size = data.get('yard_size', 2500)
    property_type = data.get('property_type', 'residential')
    additional_services = data.get('additional_services', [])
    frequency = data.get('frequency', 'once')

    # Base price calculation
    if yard_size <= 1000:
        base_price = 35
    elif yard_size <= 2500:
        base_price = 45
    elif yard_size <= 5000:
        base_price = 65
    elif yard_size <= 10000:
        base_price = 95
    else:
        base_price = 150

    # Property type adjustment
    if property_type == 'commercial':
        base_price *= 1.2

    # Additional services
    additional_cost = 0
    if 'edging' in additional_services:
        additional_cost += 15
    if 'trimming' in additional_services:
        additional_cost += 25
    if 'cleanup' in additional_services:
        additional_cost += 20

    # Calculate subtotal before discount
    subtotal = base_price + additional_cost

    # Apply frequency discount
    discount = 0
    if frequency == 'weekly':
        discount = subtotal * 0.15  # 15% discount
    elif frequency == 'biweekly':
        discount = subtotal * 0.10  # 10% discount

    total_price = round(subtotal - discount)

    return jsonify({
        'base_price': base_price,
        'additional_cost': additional_cost,
        'discount': discount,
        'subtotal': subtotal,
        'total_price': total_price,
        'success': True,
        'message': 'Quote calculated successfully'
    })


@app.route('/booking_confirmation/<int:booking_id>')
def booking_confirmation(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    # Get real weather forecast for the booking date
    date_str = booking.date.strftime('%Y-%m-%d')
    city = booking.city or DEFAULT_CITY

    # Try to get real weather data from AccuWeather
    weather_data = get_weather_for_date(city, date_str)

    # If real weather data is not available, use simulated data
    if not weather_data:
        # Generate simulated weather forecast for the booking date
        day = booking.date.day

        # Use the day number to create deterministic but varied weather
        weather_types = [
            {"icon": "sun", "description": "Sunny", "temperature": 22 + (day % 5), "precipitation": 0,
             "wind": 5 + (day % 10)},
            {"icon": "cloud-sun", "description": "Partly Cloudy", "temperature": 20 + (day % 5),
             "precipitation": 10 + (day % 15), "wind": 8 + (day % 8)},
            {"icon": "cloud", "description": "Cloudy", "temperature": 18 + (day % 5), "precipitation": 20 + (day % 20),
             "wind": 10 + (day % 10)},
            {"icon": "cloud-drizzle", "description": "Light Rain", "temperature": 16 + (day % 5),
             "precipitation": 40 + (day % 30), "wind": 12 + (day % 8)},
            {"icon": "cloud-rain", "description": "Rainy", "temperature": 14 + (day % 5),
             "precipitation": 70 + (day % 20), "wind": 15 + (day % 10)}
        ]

        weather_index = day % len(weather_types)
        weather = weather_types[weather_index]
    else:
        # Format real weather data to match template expectations
        weather = {
            "icon": get_weather_icon_class(weather_data['icon']).replace('bi-', ''),
            "description": weather_data['condition'],
            "temperature": weather_data['avg_temp'],
            "precipitation": weather_data['precipitation_probability'],
            "wind": 10  # Default value if not available
        }

        # Get lawn care recommendations
        recommendations = get_lawn_care_recommendation(weather_data)

    return render_template('confirmation.html', booking=booking, weather=weather)


@app.route('/api/available_slots', methods=['POST'])
def available_slots():
    data = request.get_json()
    selected_date_str = data.get('date')

    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # All possible slots
    all_time_slots = [
        "8:00 AM - 10:00 AM",
        "10:00 AM - 12:00 PM",
        "12:00 PM - 2:00 PM",
        "2:00 PM - 4:00 PM",
        "4:00 PM - 6:00 PM"
    ]

    # Fetch booked slots from the database
    booked_slots = db.session.query(Booking.time_slot).filter(Booking.date == selected_date).all()
    booked_slots = [slot[0] for slot in booked_slots]  # Extracting the slot values

    # Remove booked slots from available slots
    available_time_slots = [slot for slot in all_time_slots if slot not in booked_slots]

    return jsonify({'available_slots': available_time_slots})
    # Simulate some slots being unavailable
    if selected_date.endswith('01') or selected_date.endswith('15'):
        available_time_slots.remove("8:00 AM - 10:00 AM")

    return jsonify({'available_slots': available_time_slots})


# Add a new route for weather forecasts
@app.route('/api/weather_forecast', methods=['POST'])
def weather_forecast():
    data = request.get_json()
    selected_date = data.get('date')
    city = data.get('city', DEFAULT_CITY)

    # Improve city validation and logging
    if not city or not isinstance(city, str) or city.strip() == "":
        city = DEFAULT_CITY
        logger.warning(f"Invalid city provided, using default: {DEFAULT_CITY}")
    else:
        city = city.strip()  # Remove any leading/trailing whitespace
        logger.info(f"Processing weather forecast request for city: {city}")

    logger.info(f"Weather forecast requested for {city} on {selected_date}")

    # Try to get real weather data from AccuWeather
    weather_data = get_weather_for_date(city, selected_date)

    # If real weather data is available, return it
    if weather_data:
        # Add Bootstrap icon class
        weather_data['icon_class'] = get_weather_icon_class(weather_data['icon'])

        # Get lawn care recommendations
        weather_data['recommendations'] = get_lawn_care_recommendation(weather_data)

        logger.info(f"Successfully retrieved AccuWeather data for {city}")
        return jsonify({
            'success': True,
            'date': selected_date,
            'forecast': weather_data,
            'source': 'accuweather',
            'city': city
        })

    logger.warning(f"Could not get AccuWeather data for {city}, using simulated data")

    # If real weather data is not available, use simulated data
    # Parse the date string to a date object
    date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
    day = date_obj.day

    # Use the day number to create deterministic but varied weather
    weather_types = [
        {"icon": "sun", "description": "Sunny", "temperature": 22 + (day % 5), "precipitation": 0,
         "wind": 5 + (day % 10)},
        {"icon": "cloud-sun", "description": "Partly Cloudy", "temperature": 20 + (day % 5),
         "precipitation": 10 + (day % 15), "wind": 8 + (day % 8)},
        {"icon": "cloud", "description": "Cloudy", "temperature": 18 + (day % 5), "precipitation": 20 + (day % 20),
         "wind": 10 + (day % 10)},
        {"icon": "cloud-drizzle", "description": "Light Rain", "temperature": 16 + (day % 5),
         "precipitation": 40 + (day % 30), "wind": 12 + (day % 8)},
        {"icon": "cloud-rain", "description": "Rainy", "temperature": 14 + (day % 5), "precipitation": 70 + (day % 20),
         "wind": 15 + (day % 10)}
    ]

    weather_index = day % len(weather_types)
    weather = weather_types[weather_index]

    # Add lawn care suitability
    is_suitable = weather['precipitation'] < 40

    # Create simulated forecast data
    simulated_forecast = {
        'date': selected_date,
        'min_temp': weather['temperature'] - 5,
        'max_temp': weather['temperature'] + 5,
        'avg_temp': weather['temperature'],
        'condition': weather['description'],
        'icon_class': f"bi-{weather['icon']}",
        'precipitation_probability': weather['precipitation'],
        'precipitation_type': 'Rain' if weather['precipitation'] > 0 else None,
        'wind_speed': weather['wind'],
        'is_suitable_for_lawn_care': is_suitable,
        'recommendations': {
            'can_mow': is_suitable,
            'message': "Weather conditions suitable for lawn care" if is_suitable else "High chance of rain, may need to reschedule",
            'details': []
        }
    }

    # Add recommendation details based on conditions
    if is_suitable:
        if weather['temperature'] > 25:
            simulated_forecast['recommendations']['details'].append(
                "Consider mowing in the morning or evening to avoid heat")

        if weather['precipitation'] > 20:
            simulated_forecast['recommendations']['details'].append(
                "There's a slight chance of precipitation, monitor weather before service")
    else:
        simulated_forecast['recommendations']['details'].append(
            f"{weather['precipitation']}% chance of precipitation may affect service quality")

    logger.info(f"Returning simulated weather data for {city} on {selected_date}")

    return jsonify({
        'success': True,
        'date': selected_date,
        'forecast': simulated_forecast,
        'source': 'simulated',
        'city': city,
        'note': f"Weather data for {city} was not available from AccuWeather. Using simulated forecast."
    })


# Custom flowable for horizontal line with gradient
class GradientLine(Flowable):
    def __init__(self, width, height=0.5):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def draw(self):
        self.canv.saveState()
        self.canv.setLineCap(1)
        self.canv.setLineJoin(1)
        self.canv.setStrokeColor(colors.HexColor('#1eacac'))
        self.canv.setLineWidth(self.height)
        self.canv.line(0, 0, self.width, 0)
        self.canv.restoreState()


# Custom flowable for section headers with background
class SectionHeader(Flowable):
    def __init__(self, text, width, height=30):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self.height = height

    def draw(self):
        self.canv.saveState()
        # Draw background rectangle
        self.canv.setFillColor(colors.HexColor('#e6f7f7'))  # Light turquoise background
        self.canv.setStrokeColor(colors.HexColor('#1eacac'))
        self.canv.roundRect(0, 0, self.width, self.height, 5, fill=1, stroke=1)

        # Draw text
        self.canv.setFont("Helvetica-Bold", 14)
        self.canv.setFillColor(colors.HexColor('#1eacac'))
        self.canv.drawString(10, self.height / 2 - 5, self.text)
        self.canv.restoreState()


# New route to generate and download PDF quote with enhanced design
@app.route('/download_quote/<int:booking_id>')
def download_quote(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    # Create a PDF in memory
    buffer = io.BytesIO()

    # Create the PDF document with custom margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    # Get styles
    styles = getSampleStyleSheet()

    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1eacac'),  # Primary turquoise color
        spaceAfter=12,
        alignment=1  # Center alignment
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1eacac'),
        spaceAfter=6
    )

    normal_style = styles['Normal']

    # Create a style for the footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        alignment=1  # Center alignment
    )

    # Create the content for the PDF
    content = []

    # Add logo and header in a table for better layout
    # Create a table for the header with logo and title
    logo_path = os.path.join(app.static_folder, 'images/yard-portal-logo.png')

    # Check if logo exists, if not create it
    if not os.path.exists(logo_path):
        try:
            # Try to create the logo
            create_yard_portal_logo(logo_path)
        except Exception as e:
            # If logo creation fails, create a simple placeholder
            logo_path = os.path.join(app.static_folder, 'images/placeholder-logo.png')
            create_placeholder_logo(logo_path)

    # Load the logo
    logo = Image(logo_path, width=1.5 * inch, height=1.5 * inch)

    # Create a QR code for the booking
    qr_code = qr.QrCodeWidget(f"BOOKING-{booking.id}")
    qr_code_drawing = Drawing(1 * inch, 1 * inch, qr_code)

    # Create header table with logo, title and QR code
    header_data = [[logo, Paragraph("Yard Portal Service Quote", title_style), qr_code_drawing]]
    header_table = Table(header_data, colWidths=[1.5 * inch, 4 * inch, 1 * inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    content.append(header_table)
    content.append(Spacer(1, 0.25 * inch))

    # Add a quote number and date
    quote_info = [
        [Paragraph(f"<b>Quote #:</b> YPQ-{booking.id:04d}", normal_style),
         Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", normal_style)]
    ]
    quote_info_table = Table(quote_info, colWidths=[3.5 * inch, 3.5 * inch])
    quote_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9f9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))

    content.append(quote_info_table)
    content.append(Spacer(1, 0.25 * inch))

    # Add a gradient line
    content.append(GradientLine(7 * inch))
    content.append(Spacer(1, 0.25 * inch))

    # Add booking information with a section header
    content.append(SectionHeader("Customer Information", 7 * inch))
    content.append(Spacer(1, 0.1 * inch))

    # Create a table for booking details with icons
    booking_data = [
        [Paragraph("<b>Name:</b>", normal_style), Paragraph(booking.name, normal_style)],
        [Paragraph("<b>Email:</b>", normal_style), Paragraph(booking.email, normal_style)],
        [Paragraph("<b>Phone:</b>", normal_style), Paragraph(booking.phone, normal_style)],
        [Paragraph("<b>Address:</b>", normal_style), Paragraph(booking.address, normal_style)],
    ]

    booking_table = Table(booking_data, colWidths=[1.5 * inch, 5.5 * inch])
    booking_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f7f7')),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1eacac')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))

    content.append(booking_table)
    content.append(Spacer(1, 0.25 * inch))

    # Add service appointment details
    content.append(SectionHeader("Service Appointment", 7 * inch))
    content.append(Spacer(1, 0.1 * inch))

    # Create a table for service appointment details
    appointment_data = [
        [Paragraph("<b>Date:</b>", normal_style), Paragraph(booking.date.strftime('%Y-%m-%d'), normal_style)],
        [Paragraph("<b>Time:</b>", normal_style), Paragraph(booking.time_slot, normal_style)],
    ]

    appointment_table = Table(appointment_data, colWidths=[1.5 * inch, 5.5 * inch])
    appointment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f7f7')),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1eacac')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))

    content.append(appointment_table)
    content.append(Spacer(1, 0.25 * inch))

    # Add service details
    content.append(SectionHeader("Service Details", 7 * inch))
    content.append(Spacer(1, 0.1 * inch))

    # Format service type
    service_type_display = {
        'standard': 'Standard Lawn Mowing',
        'premium': 'Premium Service (Mowing + Edging)',
        'complete': 'Complete Package (Mowing + Edging + Cleanup)'
    }.get(booking.service_type, booking.service_type.title())

    # Format additional services
    additional_services_list = booking.additional_services.split(',') if booking.additional_services and isinstance(
        booking.additional_services, str) else []
    # Make sure we're working with strings, not ParagraphStyle objects
    additional_services_display = ', '.join(
        [str(s).title() for s in additional_services_list if s]) if additional_services_list else 'None'

    service_data = [
        [Paragraph("<b>Service Type:</b>", normal_style), Paragraph(service_type_display, normal_style)],
        [Paragraph("<b>Yard Size:</b>", normal_style), Paragraph(normal_style)],
        [Paragraph("<b>Yard Size:</b>", normal_style), Paragraph(f"{booking.yard_size} sq ft", normal_style)],
        [Paragraph("<b>Additional Services:</b>", normal_style), Paragraph(additional_services_display, normal_style)],
    ]

    service_table = Table(service_data, colWidths=[1.5 * inch, 5.5 * inch])
    service_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f7f7')),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1eacac')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))

    content.append(service_table)
    content.append(Spacer(1, 0.25 * inch))

    # Add pricing information
    content.append(SectionHeader("Pricing Details", 7 * inch))
    content.append(Spacer(1, 0.1 * inch))

    # Calculate base price and additional costs
    base_price = 0
    if booking.yard_size <= 1000:
        base_price = 35
    elif booking.yard_size <= 2500:
        base_price = 45
    elif booking.yard_size <= 5000:
        base_price = 65
    elif booking.yard_size <= 10000:
        base_price = 95
    else:
        base_price = 150

    # Adjust for service type
    if booking.service_type == 'premium':
        base_price += 15
    elif booking.service_type == 'complete':
        base_price += 35

    # Calculate additional services cost
    additional_cost = 0
    if 'edging' in additional_services_list and booking.service_type not in ['premium', 'complete']:
        additional_cost += 15
    if 'trimming' in additional_services_list:
        additional_cost += 25
    if 'cleanup' in additional_services_list and booking.service_type != 'complete':
        additional_cost += 20

    # Create pricing table
    pricing_data = [
        ["Item", "Description", "Amount"],
        ["Base Service", service_type_display, f"R{base_price:.2f}"],
    ]

    # Add additional services if any
    if additional_cost > 0:
        pricing_data.append(["Additional Services", additional_services_display, f"R{additional_cost:.2f}"])

    # Add total row
    pricing_data.append(["Total", "", f"R{booking.price:.2f}"])

    pricing_table = Table(pricing_data, colWidths=[1.5 * inch, 3.5 * inch, 2 * inch])
    pricing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1eacac')),  # Header row
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e6f7f7')),  # Total row
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1eacac')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#1eacac')),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#1eacac')),
    ]))

    content.append(pricing_table)
    content.append(Spacer(1, 0.25 * inch))

    # Add notes section
    content.append(SectionHeader("Important Information", 7 * inch))
    content.append(Spacer(1, 0.1 * inch))

    # Create a styled paragraph for each note
    notes = [
        "• Our team will arrive during your selected time slot",
        "• We'll text you 30 minutes before arrival",
        "• Payment will be collected after service is completed",
        "• You don't need to be home during the service",
        "• Weather conditions may affect scheduling - we'll contact you if rescheduling is needed"
    ]

    notes_style = ParagraphStyle(
        'Notes',
        parent=normal_style,
        leftIndent=10,
        spaceAfter=5
    )

    notes_content = []
    for note in notes:
        notes_content.append(Paragraph(note, notes_style))

    # Create a table for the notes with a background
    notes_table = Table([[note] for note in notes_content], colWidths=[7 * inch])
    notes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9f9')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))

    content.append(notes_table)
    content.append(Spacer(1, 0.25 * inch))

    # Add weather forecast if available
    try:
        # Get weather forecast for the booking date
        date_str = booking.date.strftime('%Y-%m-%d')
        city = booking.city or DEFAULT_CITY
        weather_data = get_weather_for_date(city, date_str)

        if weather_data:
            content.append(SectionHeader(f"Weather Forecast for {city} (Preliminary)", 7 * inch))
            content.append(Spacer(1, 0.1 * inch))

            weather_info = [
                [Paragraph("<b>Condition:</b>", normal_style),
                 Paragraph(weather_data['condition'], normal_style)],
                [Paragraph("<b>Temperature:</b>", normal_style),
                 Paragraph(f"{weather_data['avg_temp']}°C", normal_style)],
                [Paragraph("<b>Precipitation:</b>", normal_style),
                 Paragraph(f"{weather_data['precipitation_probability']}%", normal_style)]
            ]

            weather_table = Table(weather_info, colWidths=[1.5 * inch, 5.5 * inch])
            weather_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f7f7')),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1eacac')),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ]))

            content.append(weather_table)
            content.append(Spacer(1, 0.1 * inch))

            # Add weather note
            weather_note = Paragraph("Note: This is a preliminary forecast. Weather conditions may change.",
                                     notes_style)
            content.append(weather_note)
            content.append(Spacer(1, 0.25 * inch))
    except:
        # If weather data can't be retrieved, skip this section
        pass

    # Add contact information
    content.append(SectionHeader("Contact Us", 7 * inch))
    content.append(Spacer(1, 0.1 * inch))

    contact_info = [
        [Paragraph("<b>Phone:</b>", normal_style), Paragraph("(021) 555-1234", normal_style)],
        [Paragraph("<b>Email:</b>", normal_style), Paragraph("support@yardportal.co.za", normal_style)],
        [Paragraph("<b>Website:</b>", normal_style), Paragraph("www.yardportal.co.za", normal_style)],
    ]

    contact_table = Table(contact_info, colWidths=[1.5 * inch, 5.5 * inch])
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f7f7')),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1eacac')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))

    content.append(contact_table)
    content.append(Spacer(1, 0.5 * inch))

    # Add footer
    footer_text = f"Quote #{booking.id:04d} generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Thank you for choosing Yard Portal!"
    footer = Paragraph(footer_text, footer_style)
    content.append(GradientLine(7 * inch))
    content.append(Spacer(1, 0.1 * inch))
    content.append(footer)

    # Build the PDF
    doc.build(content)

    # Move to the beginning of the buffer
    buffer.seek(0)

    # Return the PDF as a downloadable file
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"yard_portal_quote_{booking_id}.pdf",
        mimetype='application/pdf'
    )


# Initialize the database
@app.before_first_request
def create_tables():
    # Check if database exists and delete it to recreate with updated schema
    db_path = 'sqlite:///yard_portal.db'
    if os.path.exists('yard_portal.db'):
        os.remove('yard_portal.db')

    # Create all tables with the updated schema
    db.create_all()

    # Add sample data if tables are empty
    if Service.query.count() == 0:
        sample_services = [
            Service(name="Lawn Mowing", description="Regular cutting to keep your lawn at the perfect height.",
                    base_price=35.0, icon="scissors"),
            Service(name="Irrigation", description="Sprinkler systems and watering solutions for a healthy lawn.",
                    base_price=75.0, icon="droplets"),
            Service(name="Landscaping", description="Transform your outdoor space with professional landscaping.",
                    base_price=150.0, icon="shovel"),
            Service(name="Leaf Removal", description="Keep your yard clean with our seasonal leaf removal service.",
                    base_price=45.0, icon="leaf")
        ]
        db.session.add_all(sample_services)

    if Testimonial.query.count() == 0:
        sample_testimonials = [
            Testimonial(name="Sarah Johnson", role="Homeowner",
                        content="Yard Portal has been taking care of my lawn for over a year now. Their service is always on time and my yard has never looked better!",
                        rating=5),
            Testimonial(name="Michael Chen", role="Property Manager",
                        content="We use Yard Portal for all our properties. Their online booking system makes scheduling easy, and their work is consistently excellent.",
                        rating=5),
            Testimonial(name="Emily Rodriguez", role="Homeowner",
                        content="I love how easy it is to get a quote and book service. The yard size estimator is spot on, and the prices are very reasonable.",
                        rating=4),
            Testimonial(name="David Thompson", role="Business Owner",
                        content="Our office building's landscaping has improved dramatically since switching to Yard Portal. Highly recommended for commercial properties.",
                        rating=5)
        ]
        db.session.add_all(sample_testimonials)

    db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)

