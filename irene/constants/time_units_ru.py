from irene.constants.gender import FEMALE, MALE
from irene.constants.word_forms import FullKnownFormsRU, KnownFormsRU

MINUTE = FullKnownFormsRU(
    singular=KnownFormsRU("минута", "минуты", "минуте", "минуту", "минутой", "минуте"),
    plural=KnownFormsRU("минуты", "минут", "минутам", "минуты", "минутами", "минутах"),
    gender=FEMALE.code,
)

HOUR = FullKnownFormsRU(
    singular=KnownFormsRU("час", "часа", "часу", "час", "часом", "часе"),
    plural=KnownFormsRU("часы", "часов", "часам", "часы", "часами", "часах"),
    gender=MALE.code,
)
