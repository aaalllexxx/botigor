import datetime
from ast import literal_eval
from dataclasses import dataclass
from fuzzywuzzy import fuzz
import string

import dotenv
import re
import json
import pymorphy2
import codecs

debug = literal_eval(dotenv.get_key(".env", "DEBUG"))
string_contains_word_score = literal_eval(dotenv.get_key(".env", "STRING_CONTAINS_WORD_SCORE"))
with open("wordlists/banwordslist.txt", encoding="utf-8") as file:
    banwords = file.read().split("\n")


def out(text, prefix='[#info]'):
    if debug:
        print(prefix + ": " + text + "  --  " + datetime.datetime.now().strftime("%H:%M:%S"))


def delete_punctuation(s: str) -> str:
    chars = '[%s]+' % re.escape(string.punctuation)
    return re.sub(chars, ' ', s)


@dataclass
class Token:
    id: int
    os: str
    name: str
    answer: str


class Recognizer:
    def __init__(self):
        self.analyzer = pymorphy2.MorphAnalyzer()
        self.alphabet = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя" + string.printable
        with open("data_json/FAQ.json", "rb") as file:
            self.data = json.loads(codecs.decode(file.read(), "utf-8-sig"))["Data"]
        self.data = sorted(self.data,
                           key=lambda x: self.alphabet.index(x["Question"][0].lower()))
        self.questions = [item["Question"].lower() for item in self.data]

    @staticmethod
    def __match(s1: str, s2: str) -> float:
        """Возвращает дробное число - очки схожести двух строк"""

        score = 0
        '''Сравниваем строки'''
        words1 = s1.split()
        for word in words1:
            for ex_word in s2.split():
                if fuzz.ratio(word, ex_word) > 75:
                    score += string_contains_word_score

        score += fuzz.ratio(s1, s2) / 100
        return score

    def __recognize(self, question):
        res = []
        for item in self.questions:
            match = self.__match(question, item)
            if match > 0.8:
                res.append(match)
            else:
                res.append(0)
        print(max(res))
        if len(list(set(res))) > 1:
            return res.index(max(res))
        else:
            return []

    def get_data(self, question):
        q_info = self.__recognize(question)
        if q_info:
            return dict(status=200, **self.data[q_info])
        else:
            return {"status": 404}
