import inspect
from dataclasses import dataclass


class Message:
    Context: dataclass

    @dataclass
    class Context:
        def __init__(self):
            raise NotImplementedError

    @classmethod
    def generator(cls, context_data: dict):
        return cls(context_data=context_data)

    @classmethod
    def _from_dict_to_dataclass(cls, context_data: dict) -> dataclass:
        return cls.Context(
            **{
                key: (context_data[key] if val.default == val.empty else context_data.get(key, val.default))
                for key, val in inspect.signature(cls.Context).parameters.items()
            }
        )

    def __init__(self, context_data: dict):
        self.Context = self._from_dict_to_dataclass(context_data=context_data)


class Command(Message):
    pass


class Event(Message):
    pass
