import json
import os
import requests
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
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
                print(members_ids)
                members_names = [get_user_info(user_id) for user_id in members_ids]
                members_emails = [get_user_email(user_id) for user_id in members_ids]
                send_group_msg("PRUEBA",members_ids)
                print(members_emails)
                return JsonResponse({'members': members_names})

            return JsonResponse({'error': 'No se pudo obtener la lista de miembros'}, status=response.status_code)

        return JsonResponse({'error': 'Evento no manejado'}, status=400)

    return JsonResponse({'error': 'Método de solicitud no válido'}, status=405)


@csrf_exempt
def slack_commands(request):
    if request.method == 'POST':
        if 'command' in request.POST:
            command = request.POST['command']
            if command == '/config-channel':
                trigger_id = request.POST.get('trigger_id')
                open_config_channel_modal(trigger_id)
                return HttpResponse(status=200)
            # elif command == '/otro-command':
            #     ...

        if 'payload' in request.POST:
            payload = json.loads(request.POST['payload'])
            # print("Payload completo:", json.dumps(payload, indent=2))
            
            callback_id = payload['view']['callback_id']
            
            if payload.get('type') == 'view_submission' and callback_id == 'config_channel_modal':
                try:
                    state_values = payload['view']['state']['values']

                    freq_days_str = state_values['meeting_frequency_days_block']['meeting_frequency_days']['value']
                    duration_str = state_values['duration_minutes_block']['duration_minutes']['value']
                    group_size_str = state_values['group_size_block']['group_size']['value']
                    user_props_str = state_values['user_properties_configuration_block']['user_properties_configuration']['value']
                    meeting_sched_str = state_values['meeting_schedule_configuration_block']['meeting_schedule_configuration']['value']

                    freq_days = int(freq_days_str) if freq_days_str.strip().isdigit() else None
                    duration = int(duration_str) if duration_str.strip().isdigit() else None
                    group_size = int(group_size_str) if group_size_str.strip().isdigit() else None
                    

                    try:
                        user_props = json.loads(user_props_str)
                    except json.JSONDecodeError:
                        user_props = user_props_str  # Si no es JSON válido, guardamos el texto tal cual

                    try:
                        meeting_sched = json.loads(meeting_sched_str)
                    except json.JSONDecodeError:
                        meeting_sched = meeting_sched_str  

                except Exception as e:
                    print("Error al extraer datos del modal:", e)

                return HttpResponse(status=200)

            return HttpResponse(status=200)

        return HttpResponseBadRequest("No es un slash command o payload válido")

    return HttpResponseBadRequest("Método no permitido")

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

def get_channel_list():
    response = requests.get(
        'https://slack.com/api/conversations.list',
        headers={'Authorization': f'Bearer {SLACK_BOT_TOKEN}'}
    )
    if response.status_code == 200:
        response = response.json().get('channels', [])
        response = [{'id': channel['id'], 'name': channel['name']} for channel in response]
        return response
    return []

def open_config_channel_modal(trigger_id):
    url = "https://slack.com/api/views.open"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "trigger_id": trigger_id,
        "view": {
            "type": "modal",
            "callback_id": "config_channel_modal",
            "title": {
                "type": "plain_text",
                "text": "Configurar Canal"
            },
            "submit": {
                "type": "plain_text",
                "text": "Guardar"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "meeting_frequency_days_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "meeting_frequency_days",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Ej: 15 (número de días)"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Frecuencia de reuniones (días)"
                    }
                },
                {
                    "type": "input",
                    "block_id": "duration_minutes_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "duration_minutes",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Ej: 30 (minutos)"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Duración (minutos)"
                    }
                },
                {
                    "type": "input",
                    "block_id": "group_size_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "group_size",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Ej: 10 (número de integrantes)"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Tamaño de grupo (group_size)"
                    }
                },
                {
                    "type": "input",
                    "block_id": "user_properties_configuration_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "user_properties_configuration",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Ingrese propiedades de usuario en formato JSON, por ejemplo: {\"rol\": \"admin\"}"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "User properties config (JSON)"
                    }
                },
                {
                    "type": "input",
                    "block_id": "meeting_schedule_configuration_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "meeting_schedule_configuration",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Ingrese la configuración de agenda en formato JSON"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Meeting schedule config (JSON)"
                    }
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=data)

def send_group_msg(msg, user_list):
    # 1️⃣ Abrir una conversación grupal
    url_open = "https://slack.com/api/conversations.open"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload_open = {
        "users": ",".join(user_list) 
    }

    response_open = requests.post(url_open, json=payload_open, headers=headers)
    data_open = response_open.json()
    
    if not data_open.get("ok"):
        print(f"Error creando grupo: {data_open.get('error')}")
        return None

    channel_id = data_open["channel"]["id"]  # ID del canal grupal

        # Enviar el mensaje al grupo
    url_msg = "https://slack.com/api/chat.postMessage"
    payload_msg = {
        "channel": channel_id,
        "text": msg
    }

    response_msg = requests.post(url_msg, json=payload_msg, headers=headers)
    data_msg = response_msg.json()

    if not data_msg.get("ok"):
        print(f"Error enviando mensaje: {data_msg.get('error')}")
    
    return data_msg