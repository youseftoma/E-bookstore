# In your app/limiter.py or where you define the limiter
from slowapi import Limiter
from slowapi.util import get_remote_address
from .config import settings

# Disable if running in a test environment
is_testing = settings.TESTING
limiter = Limiter(key_func=get_remote_address, enabled=not is_testing)
