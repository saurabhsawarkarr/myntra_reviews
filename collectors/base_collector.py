from abc import ABC, abstractmethod
from utils.file_io import save_json
from utils.logger import get_logger

class BaseCollector(ABC):
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def collect(self) -> list[dict]:
        pass

    @abstractmethod
    def validate(self, record: dict) -> bool:
        pass

    def save(self, records: list[dict], output_path: str) -> None:
        save_json(records, output_path)
        self.logger.info(f"Saved {len(records)} records to {output_path}")

    def summarize(self, records: list[dict]) -> dict:
        return {
            "total_collected": len(records),
            "valid_records": sum(1 for r in records if self.validate(r)),
        }
