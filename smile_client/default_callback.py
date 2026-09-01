import logging

from smile_client.messages.smile_message import SmileMessage

logger = logging.getLogger("smile_client")


def smile_callback(msg: SmileMessage):
    try:
        logger.info("Received a message on '{subject}': {data}".format(subject=msg.subject, data=msg.data))
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise