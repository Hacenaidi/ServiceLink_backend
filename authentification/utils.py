from twilio.rest import Client
import random
import string
import os

def send_code_to_phone(phone_number,code):
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    
    # message = client.messages.create(from_='+14243561778',body=code,to=phone_number)    
    client.messages.create(from_='+14243561778',body=code,to='+21694813197')



def generate_verification_code():
    # generate a code of 4 digits
    return ''.join(random.choices(string.digits, k=4))