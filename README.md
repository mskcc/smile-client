# SMILE Python Client

A Python client library for consuming messages from NATS JetStream in the SMILE ecosystem. This client provides both a standalone CLI tool and Django management commands for processing NATS messages with robust error handling, automatic reconnection, and graceful shutdown capabilities.

## Installation

### Prerequisites

- Python 3.6+

### Install from Source

```bash
# Clone the repository
git clone https://github.com/mskcc/smile-client.git
cd smile-client

# Install in development mode
pip install -e .
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### JSON Configuration File

Create a `config.json` file with your NATS connection parameters:

```json
{
    "NATS_URL": "nats://localhost:4222",
    "NATS_USERNAME": "your_username",
    "NATS_PASSWORD": "your_password",
    "NATS_SSL_CERTFILE": "/path/to/cert.pem",
    "NATS_SSL_KEYFILE": "/path/to/key.pem",
    "NATS_ROOT_CA": "/path/to/rootCA.pem",
    "NATS_FILTER_SUBJECT": "STREAM.consumers.*",
    "NATS_DURABLE": "your_durable_name",
    "CLIENT_TIMEOUT": 3600.0,
    "CALLBACK": "your_module.your_callback_function"
}
```

### Django Settings

For Django projects, add the configuration to your `settings.py`:

```python
SMILE_SETTINGS = {
    "NATS_URL": "nats://localhost:4222",
    "NATS_USERNAME": "your_username",
    "NATS_PASSWORD": "your_password",
    "NATS_SSL_CERTFILE": "/path/to/cert.pem",
    "NATS_SSL_KEYFILE": "/path/to/key.pem",
    "NATS_ROOT_CA": "/path/to/rootCA.pem",
    "NATS_FILTER_SUBJECT": "STREAM.consumers.*",
    "NATS_DURABLE": "your_durable_name",
    "CLIENT_TIMEOUT": 3600.0,
    "CALLBACK": "your_module.your_callback_function"
}
```

## Usage

### Command Line Interface

#### Basic Usage

```bash
# Using the installed CLI command
smile-client start_listener --config=config.json --subject=STREAM.consumers.new-requests

# Using Python module
python -m smile_client.cli start_listener --config=config.json --subject=STREAM.consumers.new-requests
```

#### With Start Date

```bash
# Start consuming from a specific date
smile-client start_listener --config=config.json --subject=STREAM.consumers.new-requests --start-date=2024-01-15
```

#### With Debug Logging

```bash
# Enable debug logging
smile-client start_listener --config=config.json --subject=STREAM.consumers.new-requests --debug
```

#### CLI Options

```
Usage:
  smile-client start_listener --config=<config_file> --subject=<subject> [--start-date=<date>] [--debug]
  smile-client (-h | --help)
  smile-client --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --config=<config_file>    Configuration file path [required].
  --subject=<subject>       NATS subject to consume from [required].
  --start-date=<date>       Start date in YYYY-MM-DD format [optional].
  --debug                   Set logging level to DEBUG [optional].
```

### Django Management Commands

#### Basic Usage

```bash
# Run the consumer (uses Django settings)
python manage.py run_smile_consumer --subject=STREAM.consumers.new-requests
```

#### With Start Date

```bash
# Start from specific date
python manage.py run_smile_consumer --subject=STREAM.consumers.new-requests --start-date=2024-01-15
```

## Writing Message Handlers

Create a custom message handler function to process incoming messages:

```python
from smile_client.messages.smile_message import SmileMessage
import logging

logger = logging.getLogger("smile_client")

def my_message_handler(msg: SmileMessage):
    """
    Process incoming SMILE messages
    
    Args:
        msg (SmileMessage): Message object containing subject and data
    """
    try:
        logger.info(f"Received message on '{msg.subject}': {msg.data}")
        
        # Your message processing logic here
        if msg.subject == "STREAM.consumers.new-requests":
            process_new_request(msg.data)
        elif msg.subject == "STREAM.consumers.updates":
            process_update(msg.data)
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise
```

Then reference it in your configuration:

```json
{
    "CALLBACK": "my_module.my_message_handler"
}
```

## Graceful Shutdown

The client supports graceful shutdown via:

- **Ctrl+C (SIGINT)**: Interactive interrupt
- **SIGTERM**: Termination signal
- **Connection errors**: Automatic cleanup on connection failures

When a shutdown signal is received:

1. Current message processing completes
2. NATS subscription is unsubscribed
3. Connection is cleanly closed
4. Process exits with proper cleanup

## Error Handling and Resilience

### Automatic Reconnection

The client automatically handles:

- **Connection drops**: Reconnects with exponential backoff
- **Network timeouts**: Retries with configurable delays
- **Server unavailability**: Continues retrying until successful

### Message Processing Errors

- Invalid JSON messages are logged and skipped
- Handler exceptions are caught and logged
- Failed messages are NAK'd for redelivery

### Configuration Options

```python
# In your SmileClient initialization
client = SmileClient({
    # ... other config ...
    "max_reconnect_attempts": 10,    # -1 for infinite
    "reconnect_delay": 5,            # seconds between retries
    "client_timeout": 3600.0         # connection timeout
})
```

## Development

### Project Structure

```
smile_client/
├── __init__.py
├── cli.py                    # Command-line interface
├── smile_client.py          # Main client class
├── default_callback.py      # Default message handler
├── messages/
│   ├── __init__.py
│   └── smile_message.py     # Message data class
└── management/
    └── commands/
        └── run_smile_consumer.py  # Django management command
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Code Style

TODO: Add this

The project uses:

- **Black** for code formatting
- **flake8** for linting

## Troubleshooting

### Common Issues

#### Import Errors

If you encounter import errors, ensure the package is properly installed:

```bash
pip install -e .
```

#### Connection Timeouts

Check your NATS server configuration and network connectivity:

```bash
# Test NATS connection
nats-cli server check --server=your-nats-server:4222
```

#### SSL/TLS Issues

Verify your certificate paths and permissions:

```bash
# Check certificate files exist and are readable
ls -la /path/to/cert.pem /path/to/key.pem /path/to/rootCA.pem
```

### Debug Logging

Enable debug logging to troubleshoot issues:

```bash
smile-client start_listener --config=config.json --subject=your-subject --debug
```

Or in your Python code:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

TODO: Decide on License

## Support

For questions or issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Open an issue on GitHub
3. Contact the development team

## Changelog

### v0.1.0
- Initial release
- NATS JetStream integration
- CLI interface with docopt
- Django management commands
- Graceful shutdown handling # TODO: Fix this
- Automatic reconnection logic
- SSL/TLS support