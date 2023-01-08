import inspect
from dataclasses import dataclass


@dataclass
class SyncEvent:
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


class EventConsumer:
    def register_handlers(self):
        for method_name in [method_name for method_name in dir(self) if method_name[0:7] == "handle_"]:
            try:
                getattr(self, method_name)()
            except TypeError:
                pass
        return self

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.register_handlers()

    def process(self, event_list: list):
        from apps.core.domain import event_registry

        for event in event_list:
            event_handler = event_registry.event_list.get(event.__class__)
            if event_handler:
                event_handler(self, context=event.Context)


class EventSender:
    event_list: list

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

        self.event_list = []


class SyncEventRegistry:
    """
    Singleton for registering sync event classes in.
    """

    def __init__(self):
        self.event_list: dict = {}

    def register(self, event: SyncEvent):
        def wrapper(func):
            def inner(*args, **kwargs):
                self.event_list[event] = func
                return func(*args, **kwargs)

            return inner

        return wrapper
