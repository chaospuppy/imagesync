from dataclasses import dataclass, field

@dataclass
class ImageCacheList:
    cache: [ImageCache] = field(default_factory=lambda: [ImageCache])

@dataclass
class ImageCache:
    name: str
    digest: str
