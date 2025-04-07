import os
import django
from django.core.files import File
from django.conf import settings
import requests
from io import BytesIO
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from rooms.models import Room

# Sample room data
rooms_data = [
    {
        'name': 'Salle de Réunion Exécutive',
        'description': 'Une salle de réunion élégante et moderne, idéale pour les réunions d\'équipe et les présentations. Équipée d\'un grand écran et d\'un système audio de haute qualité.',
        'capacity': 12,
        'price_per_hour': 150,
        'image_url': 'https://images.pexels.com/photos/1181396/pexels-photo-1181396.jpeg',
        'is_available': True,
        'amenities': ['Wi-Fi', 'Écran 65"', 'Système audio', 'Table de conférence', 'Café']
    },
    {
        'name': 'Espace de Créativité',
        'description': 'Un espace lumineux et inspirant, parfait pour les sessions de brainstorming et les ateliers créatifs. Les murs sont équipés de tableaux blancs et d\'espaces d\'affichage.',
        'capacity': 8,
        'price_per_hour': 100,
        'image_url': 'https://images.pexels.com/photos/7679725/pexels-photo-7679725.jpeg',
        'is_available': True,
        'amenities': ['Wi-Fi', 'Tableaux blancs', 'Post-it', 'Espace de détente', 'Thé et café']
    },
    {
        'name': 'Salle de Formation',
        'description': 'Une salle spacieuse conçue pour les sessions de formation et les ateliers. Équipée de tables modulaires et d\'un système de projection professionnel.',
        'capacity': 20,
        'price_per_hour': 200,
        'image_url': 'https://images.pexels.com/photos/267507/pexels-photo-267507.jpeg',
        'is_available': True,
        'amenities': ['Wi-Fi', 'Projecteur', 'Système audio', 'Tables modulaires', 'Climatisation']
    },
    {
        'name': 'Cabine de Téléconférence',
        'description': 'Une cabine insonorisée pour les appels vidéo et les réunions virtuelles. Équipée d\'un écran HD et d\'un système audio de qualité professionnelle.',
        'capacity': 4,
        'price_per_hour': 50,
        'image_url': 'https://images.pexels.com/photos/7679740/pexels-photo-7679740.jpeg',
        'is_available': True,
        'amenities': ['Wi-Fi', 'Écran HD', 'Caméra HD', 'Microphone', 'Insonorisation']
    },
    {
        'name': 'Espace de Collaboration',
        'description': 'Un espace ouvert et flexible pour le travail collaboratif. Idéal pour les équipes qui ont besoin d\'un espace de travail partagé avec des zones de concentration.',
        'capacity': 15,
        'price_per_hour': 120,
        'image_url': 'https://images.pexels.com/photos/1181435/pexels-photo-1181435.jpeg',
        'is_available': True,
        'amenities': ['Wi-Fi', 'Zones de concentration', 'Espace de détente', 'Imprimante', 'Café']
    },
    {
        'name': 'Salle de Présentation',
        'description': 'Une salle moderne et professionnelle pour les présentations importantes. Équipée d\'un grand écran 4K et d\'un système audio surround.',
        'capacity': 30,
        'price_per_hour': 250,
        'image_url': 'https://images.pexels.com/photos/416320/pexels-photo-416320.jpeg',
        'is_available': True,
        'amenities': ['Wi-Fi', 'Écran 4K', 'Système audio surround', 'Scène', 'Climatisation']
    }
]

def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return BytesIO(response.content)
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def add_sample_rooms():
    # Create media directory if it doesn't exist
    media_dir = os.path.join(settings.MEDIA_ROOT, 'room_images')
    os.makedirs(media_dir, exist_ok=True)
    
    # Clear existing rooms
    Room.objects.all().delete()
    print("Existing rooms deleted.")

    for room_data in rooms_data:
        try:
            # Create room object with amenities
            room = Room.objects.create(
                name=room_data['name'],
                description=room_data['description'],
                capacity=room_data['capacity'],
                price_per_hour=room_data['price_per_hour'],
                is_available=room_data['is_available'],
                amenities=room_data['amenities']  # Store amenities as a list directly
            )
            
            # Download and save image
            image_content = download_image(room_data['image_url'])
            if image_content:
                image_name = f"{room_data['name'].lower().replace(' ', '_')}.jpg"
                image_path = os.path.join(media_dir, image_name)
                
                with open(image_path, 'wb') as f:
                    f.write(image_content.getvalue())
                
                with open(image_path, 'rb') as f:
                    room.image.save(image_name, File(f), save=True)
            
            print(f"Added room: {room.name}")
        except Exception as e:
            print(f"Error adding room {room_data['name']}: {e}")

if __name__ == '__main__':
    add_sample_rooms() 