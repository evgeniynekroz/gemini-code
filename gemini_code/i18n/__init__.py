from .strings import i18n

def t(key: str, **kwargs) -> str:
    return i18n.t(key, **kwargs)
