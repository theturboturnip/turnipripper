#a Imports
import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

#a Classes
#c UniqueId
T = TypeVar('T', bound='UniqueId')
class UniqueId:
    class_str: ClassVar[str] = ""
    class_last : ClassVar[int] = 0
    uniq_id : int = 0
    uniq_str : str
    @classmethod
    def update_last(cls, uniq_id:int) -> None:
        if uniq_id <= cls.class_last: cls.class_last = uniq_id+1
        pass
    @classmethod
    def get_next(cls) -> int:
        n = cls.class_last
        cls.update_last(n)
        return n
    def __init__(self, uniq_id:Optional[int]=None, uniq_str:Optional[str]=None) -> None:
        if uniq_str is not None:
            self.uniq_str = uniq_str
            self.uniq_id = -1
            pass
        elif uniq_id is not None:
            self.uniq_id = uniq_id
            self.update_last(uniq_id)
            pass
        else:
            self.uniq_id = self.get_next()
            pass
        if self.uniq_id>=0:
            self.uniq_str = f"{self.class_str}.{self.uniq_id:04d}"
            pass
        pass
    def __hash__(self) -> int: return hash(self.uniq_str)
    def __lt__(self, other:T) -> bool: return self.uniq_str < other.uniq_str
    def __gt__(self, other:T) -> bool: return self.uniq_str > other.uniq_str
    def __eq__(self, other:object) -> bool:
        if not isinstance(other, UniqueId): return NotImplemented
        return self.uniq_str == other.uniq_str
    def __ne__(self, other:object) -> bool:
        if not isinstance(other, UniqueId): return NotImplemented
        return self.uniq_str != other.uniq_str
    def __le__(self, other:T) -> bool: return self.uniq_str <= other.uniq_str
    def __ge__(self, other:T) -> bool: return self.uniq_str >= other.uniq_str
    def __str__(self) -> str:
        return self.uniq_str
    def matches_uniq_id_str(self, string:str) -> bool:
        return self.uniq_str == string
    @classmethod
    def from_str(cls:Type[T], string:str) -> T:
        if string=="": return cls()
        l = len(cls.class_str)
        if l+1<len(string) and (string[:l+1] == (cls.class_str+".")):
            uniq_id = int(string[l+1:])
            return cls(uniq_id=uniq_id)
        return cls(uniq_str=string)
    pass
