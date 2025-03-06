import logging
from rich.console import Console
from rich.logging import RichHandler

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     handlers=[logging.StreamHandler()],
# )

logging.basicConfig(
    level=logging.INFO, format="%(message)s", handlers=[RichHandler(console=Console())]
)


logger = logging.getLogger(__name__)
