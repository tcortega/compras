__all__ = ["defs"]


def __getattr__(name: str):
    if name == "defs":
        from compras_ingest.definitions import defs

        return defs
    raise AttributeError(name)
