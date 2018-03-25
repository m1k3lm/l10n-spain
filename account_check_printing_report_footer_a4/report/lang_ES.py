# -*- coding: utf-8 -*-

from num2words import num2words
from num2words import CONVERTER_CLASSES, CONVERTES_TYPES
from num2words.lang_ES import Num2Word_ES


class Num2Word_ES_custom(Num2Word_ES):
    def to_currency(self, val, longval=True, old=False):
        hightxt, lowtxt = "euro/s", u"céntimo/s"
        if old:
            hightxt, lowtxt = "peso/s", "peseta/s"
        result = self.to_splitnum(val, hightxt=hightxt, lowtxt=lowtxt,
                                  divisor=1, jointxt="y", longval=longval)
        # Handle exception, in spanish is "un euro" and not "uno euro"
        return result.replace("uno", "un")


def num2words_es(number, ordinal=False, lang='en', to='cardinal', **kwargs):
    if lang not in CONVERTER_CLASSES:
        # ... and then try only the first 2 letters
        lang = lang[:2]
    if lang not in CONVERTER_CLASSES:
        raise NotImplementedError()
    if lang != 'es':
        return num2words(number, ordinal, lang, to, **kwargs)
    else:
        # Fixed implementation
        converter = Num2Word_ES_custom()
        if ordinal:
            return converter.to_ordinal(number)
        if to not in CONVERTES_TYPES:
            raise NotImplementedError()
        return getattr(converter, 'to_{}'.format(to))(number, **kwargs)
