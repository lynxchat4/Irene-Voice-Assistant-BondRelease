from irene.constants.gender import FEMALE
from irene.constants.word_forms import FullKnownFormsRU, KnownFormsRU

MINUTE = FullKnownFormsRU(
    singular=KnownFormsRU("минута", "минуты", "минуте", "минуту", "минутой", "минуте"),
    plural=KnownFormsRU("минуты", "минут", "минутам", "минуты", "минутами", "минутах"),
    gender=FEMALE.code,
)
