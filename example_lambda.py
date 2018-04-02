import faas_form

SIMPLE_SCHEMA = faas_form.Schema(
    [
        faas_form.ConstInput('event_type', value='simple', help="The user doesn't see this"),
        faas_form.StringInput('name', required=True,
                              help='Enter your name. Try "Merlin" to see advanced features'),
    ],
    instructions="Hello! Thanks for trying faas-form."
)

ADVANCED_SCHEMA = faas_form.Schema(
    [
        faas_form.ConstInput('event_type', value='advanced', help="The user doesn't see this"),
        faas_form.StringInput('required', required=True, help='Try entering an empty string, or ctrl-D'),
        faas_form.StringInput('not_required', required=False, help='Try entering an empty string, or ctrl-D'),
        faas_form.StringInput('lowercase_only', pattern=r'^[a-z]$', help='Try entering upcase letters'),
        faas_form.StringInput('with_default', default='DEFAULT_VALUE', help='If you enter an empty string or ctrl-D, a default value will be used'),
        faas_form.SecretInput('shhh', help="Tell me a secret. I won't tell!"),
        faas_form.NumberInput('num', help="Enter a float"),
        faas_form.NumberInput('num_int', integer=True, help="Try entering a non-integer value"),
        faas_form.StringListInput('strings', help='Enter an empty string or ctrl-D to terminate the list'),
        faas_form.StringListInput('strings_with_size', size=2, help='This list has to have two elements'),
        faas_form.BooleanInput('result', help="Hit y have the Lambda send a result string to display"),
        faas_form.BooleanInput('again', help="Would you like to go through this again?"),
    ],
    instructions="This is the advanced example."
)

def handler(event, context):
    print('Event:')
    print(event)
    if faas_form.is_schema_request(event):
        print('Returning simple schema')
        response = {}
        faas_form.set_schema_reponse(response, SIMPLE_SCHEMA)
    elif 'event_type' not in event:
        raise ValueError("Input event is invalid!")
    elif event['event_type'] == 'simple':
        print('Handling simple schema')
        response = handle_simple(event, context)
    else:
        print('Handling advanced schema')
        response = handle_advanced(event, context)
    print('Response:')
    print(response)
    return response

def handle_simple(event, context):
    name = event['name']
    result = 'Hello, {}!'.format(name)
    response = {}
    if name == 'Merlin':
        faas_form.set_reinvoke_response(response, ADVANCED_SCHEMA, result)
    else:
        faas_form.set_result(response, result)
    return response

def handle_advanced(event, context):
    response = {
        'received_event': event,
        'foo': 'bar',
    }
    if event['result']:
        faas_form.set_result(response, result='This is a short summary from the Lambda, instead of the response payload.')
    if event['again']:
        faas_form.set_reinvoke_response(response, ADVANCED_SCHEMA)
    return response
