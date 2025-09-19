import ssl
import json
import nats
import logging
import asyncio
import signal
from django.conf import settings
from importlib import import_module

from nats.js.api import ConsumerConfig, DeliverPolicy
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

from smile_client.messages.smile_message import SmileMessage

logger = logging.getLogger("smile_client")

class SmileClient(object):

    def __init__(self, connection_params: object = None):
        """
        :param connection_params:
        {
            "NATS_URL": <nats_url>,
            "NATS_USERNAME": <nats_username>,
            "NATS_PASSWORD": <nats_password>,
            "NATS_SSL_CERTFILE": <ssl_certfile>,
            "NATS_SSL_KEYFILE": <ssl_keyfile>,
            "NATS_ROOT_CA": <root_ca>,
            "NATS_FILTER_SUBJECT": <filter_subject>,
            "NATS_DURABLE": <nats_durable>,
            "CLIENT_TIMEOUT": <client_timeout>,
        }
        """
        smile_settings = connection_params if connection_params else getattr(settings, "SMILE_SETTINGS")
        self.servers = smile_settings.get("NATS_URL")
        self.user = smile_settings.get("NATS_USERNAME")
        self.password = smile_settings.get("NATS_PASSWORD")
        self.ssl_certfile = smile_settings.get("NATS_SSL_CERTFILE")
        self.ssl_keyfile = smile_settings.get("NATS_SSL_KEYFILE")
        self.nats_durable = smile_settings.get("NATS_DURABLE")
        self.filter_subject = smile_settings.get("NATS_FILTER_SUBJECT")
        self.nats_root_ca = smile_settings.get("NATS_ROOT_CA")
        self.client_timeout = smile_settings.get("CLIENT_TIMEOUT", 3600.0)
        self.handler_path = smile_settings.get('CALLBACK', "smile_client.default_callback.smile_callback")
        self._stop_event = asyncio.Event()

    @staticmethod
    def get_handler(handler_path) -> callable:
        """Dynamically import and return the handler function for a queue"""
        try:
            module_path, handler_name = handler_path.rsplit('.', 1)
            module = import_module(module_path)
            handler = getattr(module, handler_name)

            if not callable(handler):
                raise ValueError(f"Handler {handler_path} is not callable")

            return handler
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Could not import handler {handler_path}: {str(e)}")

    async def connect(self, subject, start_time=None):
        options = {
            "servers": self.servers,
            "user": self.user,
            "password": self.password,
            "max_reconnect_attempts": -1,
            "reconnect_time_wait": 30,
            "error_cb": self._on_error,
            "disconnected_cb": self._on_disconnected,
            "reconnected_cb": self._on_reconnected,
            "closed_cb": self._on_closed
        }

        if self.ssl_certfile and self.ssl_keyfile:
            ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
            if self.nats_root_ca:
                ssl_ctx.load_verify_locations(cafile=self.nats_root_ca)
            ssl_ctx.load_cert_chain(certfile=self.ssl_certfile, keyfile=self.ssl_keyfile)
            options["tls"] = ssl_ctx

        try:
            nc = await nats.connect(**options)

            config = {
                "filter_subject": self.filter_subject,
                "ack_policy": "explicit",
            }
            if start_time:
                config["deliver_policy"] = DeliverPolicy.BY_START_TIME
                config["opt_start_time"] = start_time
            else:
                config["deliver_policy"] = "new"

            cfg = ConsumerConfig(**config)

            js = nc.jetstream()

            sub = await js.subscribe(subject, durable=self.nats_durable, config=cfg)
            logger.info(f"Connected to NATS at {self.servers}")
            return nc, sub
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def _disconnect(self):
        try:
            if self.sub:
                await self.sub.unsubscribe()
                self.sub = None
                logger.info("Unsubscribed from NATS")

            if self.nc:
                await self.nc.close()
                self.nc = None
                logger.info("Disconnected from NATS")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self._stop_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _on_error(self, e):
        logger.error("NATS internal error: %s", e)
        self._stop_event.set()

    async def _on_disconnected(self):
        logger.warning("Disconnected from NATS")

    async def _on_reconnected(self):
        logger.info("Reconnected to NATS")

    async def _on_closed(self):
        logger.error("Connection closed permanently")
        self._stop_event.set()

    async def start_consuming(self, subject, start_date):

        self._setup_signal_handlers()

        callback = self.get_handler(self.handler_path)

        def wrapped_callback(message):
            try:
                msg_subject = message.subject
                data = json.loads(message.data.decode())
                smile_message_object = SmileMessage(msg_subject, data)
                callback(smile_message_object)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {message}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")

        while not self._stop_event.is_set():
            self.nc, self.sub = await self.connect(subject, start_date)
            logger.info("Starting consumer...")

            async for msg in self.sub.messages:
                wrapped_callback(msg)
                await msg.ack()

        logger.info("Shutdown event received, stopping consumer...")
        await self._disconnect()
