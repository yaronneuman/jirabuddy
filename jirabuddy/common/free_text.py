from shlex import shlex
from typing import List, Dict, Any, Optional, Callable, Tuple

from jirabuddy.common.enum import TypeWrapper


class FreeTextParser(object):
    def __init__(self, case_sensitive=False):
        self.case_sensitive = case_sensitive
        self._store: Dict[str, Callable] = {}
        self._ignored_terms: List[str] = []
        self.priorities: List[str] = []

    @staticmethod
    def shlexit(text: str, sep: str = '`'):
        lex = shlex(text)
        lex.quotes = sep
        lex.wordchars += "<@>=,"
        return [lx.replace(sep, "") for lx in list(lex)]

    @staticmethod
    def to_cases(var: [str, List[str]], do_cases=True) -> List[str]:
        if not isinstance(var, list):
            var = [var]

        if not do_cases:
            return var

        _cases = []
        for text in var:
            _cases += [text, text.lower(), text.upper(), text.capitalize(), text.title()]

        return _cases

    def register(self, name: str, func: Callable, priority: Optional[int] = None):
        self._store[name] = func
        if priority is None:
            self.priorities.append(name)
        else:
            self.priorities.insert(priority, name)

    def register_enum(self, enum: TypeWrapper, priority: Optional[int] = None) -> None:
        self.register(enum.__name__, enum.__getitem__, priority)

    def ignore(self, *terms) -> None:
        self._ignored_terms += terms

    def parse(self, text: str) -> Tuple[Dict[str, Any], List[str]]:
        results = {}
        could_not_found = []

        for phrase in self.shlexit(text):

            # ignore phrase
            if phrase in self.to_cases(self._ignored_terms, not self.case_sensitive):
                continue

            # phrase is key=value, don't search by priorities
            if len(phrase.split("=")) == 2:
                key, value = phrase.split("=")
                try:
                    results[key] = self._store[key](value)
                except Exception:
                    results[key] = value
                continue

            phrase_not_found = True
            for p in self.priorities:
                for cased_phrase in self.to_cases(phrase, not self.case_sensitive):
                    if results.get(p) is None:
                        try:
                            res = self._store[p](cased_phrase)
                            if res:
                                results[p] = (res, phrase)
                                phrase_not_found = False
                        except Exception:
                            continue

            if phrase_not_found:
                could_not_found.append(phrase)

        return results, could_not_found
