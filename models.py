from dataclasses import dataclass, asdict, field
from pathlib import Path

@dataclass
class Book:
    name: str
    title_book: str
    author_first: str
    author_last: str
    folder: str = field(repr=False)
    book_name_txt: str = field(repr=False)
    book_image: str = field(repr=False, default='')
    annotation: str = field(repr=False, default='')

    @property
    def fullname(self):
        author = (self.author_first.strip() + ' ' + self.author_last).strip()
        name = author + ('. ' if author else '') + self.title_book.strip()
        return name

    @classmethod
    def empty_book(cls):
        return cls('', '', '', '', '', '')

    @classmethod
    def from_dict(cls, d: dict) -> "Book":
        return cls(name=d['name'],
                   title_book=d['title_book'],
                   author_first=d['author_first'],
                   author_last=d['author_last'],
                   annotation=d['annotation'],
                   folder=d['folder'],
                   book_name_txt=d['book_name_txt'],
                   book_image=d['book_image']
                   )

    def to_dict(self) -> dict:
        return asdict(self)

    def copy(self):
        return Book.from_dict(self.to_dict().copy())

    def is_valid(self) -> bool:
        if (self.name and self.author_first and self.author_last and self.title_book and
                self.folder and self.book_name_txt and (Path(self.folder) / self.book_name_txt).exists()):
            return True
        return False
