import inspect
import uuid
from dataclasses import dataclass


class Message:
    uuid = str
    Context: dataclass

    @dataclass
    class Context:
        def __init__(self):
            raise NotImplementedError

    @classmethod
    def generator(cls, context_data: dict):
        obj = cls(context_data=context_data)
        print(f"Creating message '{cls.__name__}' ({obj.uuid}) with {str(context_data)}.")
        return obj

    @classmethod
    def _from_dict_to_dataclass(cls, context_data: dict) -> dataclass:
        return cls.Context(
            **{
                key: (context_data[key] if val.default == val.empty else context_data.get(key, val.default))
                for key, val in inspect.signature(cls.Context).parameters.items()
            }
        )

    def __str__(self) -> str:
        return f"{self.__class__} ({self.uuid})"

    def __init__(self, context_data: dict):
        self.uuid = str(uuid.uuid4())
        self.Context = self._from_dict_to_dataclass(context_data=context_data)


class Command(Message):
    pass


class Event(Message):
    pass
