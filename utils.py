import secrets
import string

def generate_password(length):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))


def generate_code(length):
    alphabet = string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))