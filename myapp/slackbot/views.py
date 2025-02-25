import json
import os
import requests
import schedule
import time
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

load_dotenv()  # Cargar las variables del archivo .env

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")


@csrf_exempt
def slack_events(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        #PARA VERIFICAR LA URL EN SLACK
        if 'challenge' in data:
            return JsonResponse({'challenge': data['challenge']})
        

        if 'event' in data and data['event']['type'] == 'app_mention':
            channel_id = data['event']['channel']

            response = get_channel_info(channel_id)

            if response.status_code == 200:
                members_ids = response.json().get('members', [])
                members_names = [get_user_info(user_id) for user_id in members_ids]
                members_emails = [get_user_email(user_id) for user_id in members_ids]

                print(members_emails)
                return JsonResponse({'members': members_names})

            return JsonResponse({'error': 'No se pudo obtener la lista de miembros'}, status=response.status_code)

        return JsonResponse({'error': 'Evento no manejado'}, status=400)

    return JsonResponse({'error': 'Método de solicitud no válido'}, status=405)

def get_channel_info(channel_id):
    response = requests.get(
        f'https://slack.com/api/conversations.members?channel={channel_id}',
        headers={'Authorization': f'Bearer {SLACK_BOT_TOKEN}'}
    )
    return response

def get_user_info(user_id):
    response = requests.get(
        f'https://slack.com/api/users.info?user={user_id}',
        headers={'Authorization': f'Bearer {SLACK_BOT_TOKEN}'}
    )
    if response.status_code == 200:
        return response.json().get('user', {}).get('real_name', 'Desconocido')
    return 'Desconocido'

def get_user_email(user_id):
    response = requests.get(
        f'https://slack.com/api/users.info?user={user_id}',
        headers={'Authorization': f'Bearer {SLACK_BOT_TOKEN}'}
    )
    if response.status_code == 200:
        user_info = response.json().get('user', {})
        return user_info.get('profile', {}).get('email', 'Desconocido')
    return 'Desconocido'
