from django import template

register = template.Library()


@register.filter()
def censor(value):
    if not isinstance(value, str):
        return value

    bad_words = [
        'редиска', 'негодяй', 'мерзкий', 'гнусный', 'скверный', ]

    result = value

    for word in bad_words:
        stars = '*' * len(word)
        result = result.replace(word, stars)
        result = result.replace(word.capitalize(), stars)

    return result