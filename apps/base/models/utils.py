# apps/base/models/utils.py
from .middleware import _thread_locals

def get_current_user():
    return getattr(_thread_locals, 'user', None)